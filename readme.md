# 你只需要出刀（KCR 环奈连结R）

## <font color=#FF0000>严重警告</font>

### 真要命！！！，本插件过于方便，优雅，简单，可能会危及公会战，"管理困难"，"BOX不对"这些经久不衰的重要功能。本人建议各大公会将本插件列为<font color=#FF0000>禁用</font>插件。

## 项目地址：

https://github.com/SonderXiaoming/kanna_connection_redive

## 基本说明(世界的起点，账号绑定)

* #### “+” 表示空格（除非特别说明，否则默认为空格）

```
加机器人好友，私聊【绑定账号+账号+密码】加号为空格
```

 <details><summary><font size=5 >1. 自动报刀</font></summary>
【出刀监控】机器人登录账号，监视出刀情况并记录<br>
【催刀】栞栞谁没出满三刀<br>
【当前战报】本期会战出刀情况<br>
【我的战报 + 游戏名称】 栞栞个人出刀情况<br>
【今日战报 + 游戏名称】 栞栞今日个人出刀情况<br>
【昨日战报 + 游戏名称】 栞栞昨日个人出刀情况<br>
【出刀详情 + 出刀编号】 栞栞你这刀怎么出的（出刀编号可以通过查看个人战报获得）<br>
【今日出刀】今日出刀情况<br>
【昨日出刀】昨日出刀情况<br>
【启用肃正协议】数据出现异常使用即可清空所有数据（危险！！！）<br>
【修正出刀 + 出刀编号 + （完整刀|尾刀|补偿）】修正错误的刀数记录<br>
【状态】查看当前进度<br>
【boss状态】看看boss里面有几个人<br>
【预约表】栞栞谁预约了<br>
【预约 + 数字 + （周目）+ （留言） 】预约boss, 周目和留言可不写，默认当前周目<br>
【取消预约 + （数字）】取消预约<br>
【清空预约 + （数字）】（仅）管理，清空预约<br>
【查树】栞栞树上有几个人<br>
【下树】寄，掉刀了<br>
【挂树 + 数字】失误了, 寄<br>
【sl】记录sl<br>
【sl?】栞栞今天有没有用过sl<br>
【申请出刀 + 数字 + （留言） 】 申请打boss，boss死亡自动清空<br>
【取消申请】 模拟10次挂10次，老子不打了</details>

 <details><summary><font size=5 >2. BOX查询(可查会战助战)</font></summary>
【刷新box缓存】会顶号，请注意，机器人自动上号记录你的box<br>
【box查询+角色名字】（@别人可以查别人，角色名输入【所有】则都查）<br>
【绑定本群公会】将自己绑定在这个群<br>
【删除本群公会绑定】将自己踢出公会（管理可以at别人实现踢人效果）<br>
【公会box查询+角色名字】查询绑定公会的玩家的box，不支持输入所有（卡不死你）<br>
【刷新助战缓存】会顶号，请注意，机器人自动上号记录公会助战<br>
【精确助战+角色名字】（角色名输入【所有】则都查）<br>
</details>

 <details><summary><font size=5 >3. 分刀（自动分刀待修）</font></summary>
分刀 [阶段] [毛分/毛伤] (类型) (BOSS) <br>
阶段：ABCD，对应公会战的四个阶段，支持跨面，如‘CCD’，和后面boss一一对应，只填写一个默认全是这一阶段 <br>
类型：T 代表自动刀，W 代表尾刀，S代表手动刀，填写多个代表都行，留空表示我全要 <br>
BOSS：1-5，对应公会战的一至五王，可以‘123’或者‘12’,也可以‘555’,留空表示哪个boss无所谓 <br>
作业序号：列表中作业的序号 <br>
 <br>
指令示例： <br>
分刀 A 毛分 <br>
(查询一阶段的所有分刀可能，按分数排序) <br>
分刀 A 毛分 123 <br>
(查询一阶段的1,2,3王所有分刀可能，按分数排序) <br>
分刀 A 毛分 T  <br>
(查询一阶段一王的AUTO刀所有分刀可能，按分数排序) <br>
分刀 A 毛分 T 123 <br>
(查询一阶段的1,2,3王所有AUTO刀分刀可能，按分数排序) <br>
注：指令示例中的空格均不可省略。 <br>
 <br>
【添加角色黑名单】 + 角色名称 <br>
（支持多角色，例如春环环奈，无空格） <br>
【添加角色缺失】 + 角色名称 <br> 
（支持多角色，例如春环环奈，无空格） <br>
【删除角色黑名单】 + 角色名称 <br>
（支持多角色，例如春环环奈，无空格） <br>
【删除角色缺失】 + 角色名称 <br>
（支持多角色，例如春环环奈，无空格） <br>
【删除作业黑名单】 + 作业id <br>
【添加作业黑名单】 + 作业id <br>
【查看角色缺失】（查看哪些角色缺失） <br>
【查看角色黑名单】（查看哪些角色是黑名单） <br> <br>
【查看作业黑名单】（查看哪些作业是黑名单） <br>
【清空角色缺失】（清空角色缺失） <br>
【清空角色黑名单】（清空角色黑名单） <br>
【清空作业黑名单】（清空作业黑名单） <br>
数据来源于: https://www.caimogu.cc/gzlj.html
</details>
## BOX图效果展示

![box图](https://raw.githubusercontent.com/SonderXiaoming/kanna_connection_redive/master/show_img/box.png)

## 简单食用教程：

1. 安装前置插件[multicq_send](https://github.com/SonderXiaoming/multicq_send)，[convert2img](https://github.com/SonderXiaoming/convert2img)，无需加载

2. 下载或git clone本插件：

   在 HoshinoBot\hoshino\modules 目录下使用以下命令拉取本项目

   ```
   git clone https://github.com/SonderXiaoming/kanna_connection_redive
   ```

3. 在 HoshinoBot\hoshino\config\ `__bot__.py` 文件的 MODULES_ON 加入 'kanna_connection_redive'

4. 然后重启 HoshinoBot

## TODO

1. 网页端支持（会vue的广快过来）
2. 更多插件代码说明，方便代码水平有待提升的后进牲更好的pr
3. 会战时补上会战效果图（等pr吧，用过花舞bot应该都知道，不知道就买一个）

## 更新日志

1.0.0 好的开始