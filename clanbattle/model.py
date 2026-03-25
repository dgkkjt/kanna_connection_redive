import os
import traceback
import time
import asyncio
from datetime import datetime
from .base import CancleError, find_item, format_bignum, format_precent, clan_path
from .sql import RecordDao, SubscribeDao, TreeDao, ApplyDao, RankingDao
from ..util.tools import load_config, write_config, lap2stage, stage_dict


# 全局排名数据库实例（所有群共享）
_global_ranking_dao = None

def get_ranking_dao():
    """获取全局排名数据库实例"""
    global _global_ranking_dao
    if _global_ranking_dao is None:
        _global_ranking_dao = RankingDao()
    return _global_ranking_dao


class ClanBattle:
    def __init__(self, group_id) -> None:
        self.rank = 0  # 会战排名
        self.period = 0  # 阶段
        self.lap_num = 0  # 周目（会战周目，boss可能多一周目）
        self.loop_num = 0  # 循环编号
        self.error_count = 0  # 失败计数
        self.loop_check = False  # 循环检查
        self.group_id = group_id
        self.qq_id = None  # 用户QQ ID
        self.notice_dao = []
        self.notice_tree = []
        self.notice_fighter = []
        self.notice_subscribe = []
        self.boss = [Boss(), Boss(), Boss(), Boss(), Boss()]

    def init_database(self):
        self.record = RecordDao(self.group_id)
        self.subscribe = SubscribeDao(self.group_id)
        self.tree = TreeDao(self.group_id)
        self.apply = ApplyDao(self.group_id)
        self.ranking = get_ranking_dao()  # 全局共享的排名数据库
        self.last_ranking_minute = -1  # 记录上次执行排名获取时的分钟号，用于判断是否已执行过

    async def init(self, client, qq_id):
        try:
            self.loop_num += 1
            self.client = client  # api client
            self.qq_id = qq_id
            home_index = await self.client.callapi('/home/index', {'message_id': 1, 'tips_id_list': [], 'is_first': 1, 'gold_history': 0})
            load_index = await self.client.callapi('/load/index', {'carrier': 'OPPO'})
            self.clan_id = home_index['user_clan']['clan_id']
            self.user_name = load_index['user_info']['user_name']
            clan_battle_top = await self.get_clanbattle_top()
            self.clan_battle_id = clan_battle_top["clan_battle_id"]
            self.lap_num = clan_battle_top["lap_num"]
            self.period = stage_dict[lap2stage(self.lap_num)]
            self.refresh_latest_time(clan_battle_top)
            self.init_database()
            # 记录群成员
            await self.save_member(os.path.join(clan_path, f'{self.group_id}', "clanbattle.json"))
        except Exception as e:
            print(traceback.format_exc())
            raise Exception(f"数据库初始化失败 + {str(e)}")

    async def get_coin(self):
        load_index = await self.client.callapi('/load/index', {'carrier': 'OPPO'})
        return find_item(load_index["item_list"], 90006)

    async def get_clanbattle_top(self):
        return await self.client.callapi('/clan_battle/top', {"clan_id": self.clan_id, "is_first": 0, "current_clan_battle_coin": await self.get_coin()})

    async def save_member(self, config_file):
        member_dict = {}
        members = await self.client.callapi('/clan/info', {'clan_id': self.clan_id, 'get_user_equip': 0})
        for member in members["clan"]["members"]:
            member_dict[member["name"]] = member["viewer_id"]
        config = dict(await load_config(config_file))
        config["member"] = member_dict
        await write_config(config_file, config)

    async def refresh_fighter_num(self, lap_num, order):
        boss: Boss = self.boss[order-1]
        try:
            if boss.check_available(lap_num, self.period):  # 不能超过两个周目，不能跨阶段
                reload_detail_info = await self.client.callapi('/clan_battle/reload_detail_info',
                                                               {"clan_id": self.clan_id, "clan_battle_id": self.clan_battle_id, "lap_num": lap_num, "order_num": order})
                reload_detail_info["fighter_num"]
                if reload_detail_info["fighter_num"] != boss.fighter_num:
                    boss.fighter_num = reload_detail_info["fighter_num"]
                    return reload_detail_info["fighter_num"]
        except Exception:
            return 0
        return 0  # 0不播报，没改变不报，改变了是0也不报

    async def get_battle_log(self, page):
        return await self.client.callapi('/clan_battle/battle_log_list',  {
            "clan_battle_id": self.clan_battle_id,
            "order_num": 0,
            "phases": [1, 2, 3, 4],
            "report_types": [1, 2, 3],
            "hide_same_units": 0,
            "favorite_ids": [],
            "sort_type": 4,
            "page": page,
        }
        )

    async def fetch_period_ranking(self, page):
        """获取指定页码的排名数据"""
        return await self.client.callapi('/clan_battle/period_ranking', {
            'clan_id': self.clan_id,
            'clan_battle_id': self.clan_battle_id,
            'period': 1,
            'month': 0,
            'page': page,
            'is_my_clan': 0,
            'is_first': 1
        })

    async def record_period_ranking(self, current_qq_id):
        """整点过1分钟和半小时过1分钟定期获取并记录排名前60名的数据
        
        Args:
            current_qq_id: 当前监控的qq_id
        
        注：仅当 current_qq_id 为全局指定的排名获取账号时才执行
        执行时间：每小时的第1分钟和第31分钟（如12:01、12:31、13:01、13:31等）
        """
        try:
            # 导入全局变量进行检查
            from . import ranking_fetch_qq_id
            
            # 只有全局指定的账号才能执行排名获取，避免所有账号重复获取
            if ranking_fetch_qq_id is None or ranking_fetch_qq_id != current_qq_id:
                return
            
            # 检查当前时间是否为整点过1分钟或半小时过1分钟
            now = datetime.now()
            current_minute = now.minute
            current_second = now.second
            
            # 只在第1分钟或第31分钟执行（XX:01 或 XX:31）
            if current_minute not in (1, 31):
                return
            
            # 如果当前分钟已在本周期内执行过，则跳过（避免重复执行）
            # 当分钟号改变时（从1->31 或 31->1），自动重置执行状态
            if self.last_ranking_minute == current_minute:
                return
            
            # 标记当前分钟已执行
            self.last_ranking_minute = current_minute
            
            current_time = time.time()
            ranking_data = []
            timestamp = int(current_time)
            
            # 获取前6页（每页10名，共60名）
            for page in range(6):
                try:
                    ranking_info = await self.fetch_period_ranking(page)
                    if not ranking_info or 'period_ranking' not in ranking_info:
                        break
                    
                    for clan_info in ranking_info['period_ranking']:
                        rank = clan_info.get('rank', 0) # API中没有直接返回，用0作为占位符
                        clan_name = clan_info.get('clan_name', '')
                        leader_id = clan_info.get('leader_viewer_id', 0)
                        leader_name = clan_info.get('leader_name', '')
                        damage = clan_info.get('damage', 0)
                        
                        ranking_data.append((
                            rank, clan_name, leader_id, leader_name, damage, timestamp
                        ))
                except Exception as e:
                    print(f"获取排名页{page}失败: {str(e)}")
                    continue
                
                # 每次API调用间隔短暂延迟，避免过快请求
                await asyncio.sleep(0.5)
            
            # 保存排名数据到数据库
            if ranking_data:
                await self.save_ranking(ranking_data)
        except Exception as e:
            print(f"记录排名数据失败: {traceback.format_exc()}")

    async def save_ranking(self, ranking_data):
        """保存排名数据到数据库"""
        try:
            self.ranking.add_ranking(ranking_data)
        except Exception as e:
            print(f"保存排名数据到数据库失败: {str(e)}")

    async def add_record(self, damage_history, loop_num):
        log_list = []
        dao_list = []
        try:
            log_temp = await self.get_battle_log(1)  # 获取最大页数
            if not log_temp["battle_list"]:
                return  # 数据空

            max_page = log_temp["max_page"]
            latest_time = self.record.get_latest_time()
            for page in range(max_page, 0, -1):
                log = await self.get_battle_log(page)
                if log["battle_list"][-1]["battle_end_time"] > latest_time:
                    log_list += log["battle_list"][::-1]
                else:
                    break

            for record in log_list[::-1]:
                if loop_num != self.loop_num:
                    raise CancleError

                if (time := record["battle_end_time"]) > int(latest_time) and record["battle_type"] == 1:
                    pcrid = record["target_viewer_id"]
                    name = record["user_name"]
                    boss = record["order_num"]
                    lap = record["lap_num"]
                    damage = record['total_damage']
                    battle_log_id = record['battle_log_id']
                    units_list = [0 for i in range(30)]
                    for i, unit in enumerate(record["units"]):
                        units_list[i] = unit["unit_id"]
                        units_list[i + 5] = unit["unit_level"]
                        units_list[i + 10] = unit["damage"]
                        units_list[i + 15] = unit["unit_rarity"]
                        units_list[i + 20] = unit["promotion_level"]
                        units_list[i + 25] = unit["unique_equip_slot"][0]["enhancement_level"] if unit["unique_equip_slot"] else 0
                    # 故意不重试，这循环极端情况下运行10分钟也正常，不如报错趁早退出，下次再来
                    time_line = await self.client.callapi('/clan_battle/timeline_report', {"target_viewer_id": pcrid, "clan_battle_id": self.clan_battle_id, "battle_log_id": battle_log_id})
                    remain_time, battle_time = time_line["start_remain_time"], time_line["battle_time"]
                    '''flag = 0 if remain_time == 90 else 0.5
                    if battle_time < 90 and flag == 0:
                        flag = 1
                        if damage_history[-1]["create_time"] <= time <= damage_history[0]["create_time"]:
                            for history in damage_history:
                                if history["create_time"] == time and not history["kill"]:
                                    flag = 0
                                    break'''
                    ############################new#############################################################
                    # flag: 1=尾刀, 0.5=补偿刀, 0=完整刀
                    if remain_time < 90:
                        if battle_time < 90:
                            flag = 0.5  # 补偿刀
                        else:
                            flag = 1
                    else: # remain_time == 90
                        flag = 0 # 默认为完整刀
                        # 检查是否为用时90秒的尾刀
                        if damage_history[-1]["create_time"] <= time <= damage_history[0]["create_time"]:
                            for history in damage_history:
                                if history["create_time"] == time and history["kill"]:
                                    flag = 1  # 确认是尾刀
                                    break
                    ############################new#############################################################       
                    # FIXME:开销有点大
                    
                    # 伤害修正开始
                    if flag == 1:
                        damage_report = await self.client.callapi('/clan_battle/damage_report', {'clan_id': int(self.clan_id), 'clan_battle_id': int(self.clan_battle_id), 'lap_num': int(lap), 'order_num': int(boss)})
                        for it in damage_report['damage_report']:
                            if it.get('viewer_id') == pcrid:
                            #if pcrid in it:
                                damage_fix = it['damage']
                                past_damage = self.record.get_past_damage(lap, boss, pcrid)
                                if damage_fix > damage and past_damage > 0:
                                    damage = damage_fix - past_damage
                                    break
                                else:
                                    damage = damage_fix
                                    break
                    # 伤害修正结束
                    

                    dao_list.append((pcrid, name, time, lap, boss, damage, flag,
                                    battle_log_id, remain_time, battle_time, *units_list))
        except:
            pass
        await self.record.add_record(dao_list)

    def refresh_latest_time(self, clan_battle_top):
        try:
            self.latest_time = clan_battle_top["damage_history"][0]["create_time"]
        except:
            self.latest_time = 0

    def general_boss(self):
        return "当前进度：" + f"{lap2stage(self.lap_num)}面{self.period}阶段\n" + "\n".join([boss.boss_info(self.lap_num, self.period) for boss in self.boss])


class Boss:
    def __init__(self) -> None:
        self.stage = 0
        self.order = 0
        self.max_hp = 0
        self.lap_num = 0
        self.stage_num = 0
        self.current_hp = 0
        self.fighter_num = 0

    def refresh(self, current_hp, lap_num, order, max_hp):
        self.current_hp = current_hp
        self.lap_num = lap_num
        self.order = order
        self.max_hp = max_hp
        self.stage = lap2stage(lap_num)
        self.stage_num = stage_dict[self.stage]

    def boss_info(self, lap_num, period):
        msg = f'{self.lap_num}周目{self.order}王: '
        if self.check_available(lap_num, period) and self.current_hp:
            msg += f'HP: {format_bignum(self.current_hp)}/{format_bignum(self.max_hp)} {format_precent(self.current_hp/self.max_hp)}'
            if self.fighter_num:
                msg += f" 当前有{self.fighter_num}人挑战"
        else:
            msg += "无法挑战"
        return msg

    def check_available(self, lap_num, period):
        return self.lap_num - lap_num < 2 and self.stage_num == period
