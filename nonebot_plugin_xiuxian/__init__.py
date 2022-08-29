import re
from itertools import chain
from nonebot.log import logger
from nonebot import get_driver
from nonebot import on_command,require,on_message
from nonebot.params import CommandArg, RawCommand,Depends, Arg, ArgStr, RegexMatched
from nonebot.adapters.onebot.v11 import Bot, Event, GROUP, GROUP_ADMIN, GROUP_OWNER, Message, MessageEvent, GroupMessageEvent,MessageSegment
from .xiuxian_handle import linggen_get,BreadDataManage
from .xiuxian2_handle import XiuxianDateManage
from datetime import datetime
import random
from .xiuxian_opertion import gamebingo

scheduler = require("nonebot_plugin_apscheduler").scheduler


__xiuxian_version__ = "v0.0.1"
__xiuxian_notes__ = f'''
修仙模拟器帮助信息:
指令：
1、我要修仙：进入修仙模式
2、我的修仙信息：获取修仙数据
3、修仙签到：获取灵石及修为
4、重入仙途：重置灵根数据，每次100灵石
5、#金银阁：猜大小，赌灵石
6、改名xx：修改你的道号，暂无用户，待排行榜使用
7、其他功能to do中 
'''.strip()

driver = get_driver()


run_xiuxian = on_command('我要修仙',priority=5)
xiuxian_message = on_command('我的修仙信息',aliases={'我的存档'},priority=5)
rename = on_command('改名',priority=5)
restart = on_command('再入仙途',aliases={'重新修仙'},priority=5)
package = on_command('我的纳戒',aliases={'升级纳戒'},priority=5)
sign_in = on_command('修仙签到',priority=5)
dufang = on_command('#金银阁',aliases={'金银阁'},priority=5)
dice = on_command('大',aliases={'小'},priority=5)
price = on_command('押注',priority=5)
help_in = on_command('修仙帮助',priority=5)
remaker = on_command('重入仙途',priority=5)
use = on_command('#使用',priority=5)
buy = on_command('#购买',priority=5)
power_rank = on_command('修仙排行',priority=5)
ls_rank = on_command('灵石排行',priority=5)
time_mes = on_message(priority=100)
remaname = on_command('改名',priority=5)
pojing = on_command('突破',priority=5)
biguan = on_command('闭关',priority=5)

race = {}
sql_message = XiuxianDateManage()

@run_xiuxian.handle()
async def _(bot: Bot, event: GroupMessageEvent,args: Message = CommandArg()):
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    # text = args.extract_plain_text().strip()   获取命令后面的信息
    user_name = event.sender.card if event.sender.card else event.sender.nickname
    name, type = linggen_get()
    rate  = sql_message.get_type_power(type)
    power = 100 * float(rate)
    create_time = str(datetime.now())

    msg = sql_message.create_user(user_id,name,type,int(power),create_time,user_name)
    await run_xiuxian.finish(msg,at_sender=True)

@xiuxian_message.handle()
async def _(event: GroupMessageEvent):
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())


    mess = sql_message.get_user_message(user_id)
    if mess:
        msg = f'''你的灵根为：{mess[3]}
灵根类型为：{mess[4]}
当前境界：{mess[5]}
当前灵石：{mess[2]}
你的战力为：{mess[6]}'''
    else:
        msg = '未曾踏入修仙世界，输入 我要修仙 加入我们，看破这世间虚妄!'

    await run_xiuxian.finish(msg,at_sender=True)

@sign_in.handle()
async def _(event: GroupMessageEvent):
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    result = sql_message.get_sign(user_id)
    await sign_in.send(result, at_sender=True)


@help_in.handle()
async def _(event: GroupMessageEvent):
    msg = __xiuxian_notes__
    await help_in.send(msg, at_sender=True)

@dice.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg(), cmd: Message = RawCommand()):
    global race
    message = event.message
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    try:
        race[group_id]
    except KeyError:
        await price.finish()

    if race[group_id].player[0] == user_id:
        pass
    else:
        await dice.finish('吃瓜道友请不要捣乱！！！')

    price_num = race[group_id].price
    value = random.randint(1,6)
    msg = Message("[CQ:dice,value={}]".format(value))
    if value>=4:
        if str(message)=='大':
            del race[group_id]
            sql_message.update_ls(user_id,price_num,1)
            await dice.send(msg)
            await dice.finish('最终结果为{}，你猜对了，收获灵石{}块'.format(value,price_num),at_sender=True)
        else:
            del race[group_id]
            sql_message.update_ls(user_id, price_num, 2)
            await dice.send(msg)
            await dice.finish('最终结果为{}，你猜错了，损失灵石{}块'.format(value, price_num),at_sender=True)
    elif value<=3:
        if str(message)=='大':
            del race[group_id]
            sql_message.update_ls(user_id, price_num, 2)
            await dice.send(msg)
            await dice.finish('最终结果为{}，你猜错了，损失灵石{}块'.format(value, price_num),at_sender=True)
        else:
            del race[group_id]
            sql_message.update_ls(user_id, price_num, 1)
            await dice.send(msg)
            await dice.finish('最终结果为{}，你猜对了，收获灵石{}块'.format(value, price_num),at_sender=True)


@dufang.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message=CommandArg(), cmd: Message=RawCommand()):
    global race
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    user_message = sql_message.get_user_message(user_id)
    if user_message:
        if user_message.stone==0:
            await price.finish(f"道友的灵石太少，速速退去！", at_sender=True)
    else:
        await price.finish(f"本阁没有这位道友的信息！输入【我要修仙】加入吧！", at_sender=True)

    try:
        if race[group_id].start == 1 and race[group_id].player[0] == user_id:
            await dufang.finish(f"道友的活动已经开始了，发送【押注+数字】参与")
        elif race[group_id].start == 1 and race[group_id].player[0] != user_id:
            await dufang.finish(f"已有其他道友进行中")
    except KeyError:
        pass
    race[group_id] = gamebingo()
    race[group_id].start_change(1)
    race[group_id].add_player(user_id)
    race[group_id].time = datetime.now()
    await dufang.finish(f'发送【押注+数字】参与',at_sender=True)


@price.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message=CommandArg(), cmd: Message=CommandArg()):
    global race
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    msg = args.extract_plain_text().strip()

    user_message = sql_message.get_user_message(user_id)
    try:
        race[group_id]
    except KeyError:
        await price.finish(f"金银阁未开始，请输入“#金银阁”开场",at_sender=True)
    try:
        if race[group_id].player[0] == user_id:
            pass
        else:
            await price.finish('吃瓜道友请不要捣乱！')
    except KeyError:
        await price.finish()
    if msg:
        price_num = msg
        if race[group_id].price != 0:
            await price.finish('钱财离手，不可退回！', at_sender=True)
        elif int(user_message.stone) < int(price_num):
            await price.finish('道友的金额不足，请重新输入！')
        elif price_num.isdigit():
            race[group_id].add_price(int(price_num))
        else:
            await price.finish('请输入正确的金额！')
    else:
        await price.finish(f"请输入押注金额", at_sender=True)

    out_msg = f'押注完成，发送【大】或者【小】 参与本局游戏！'
    await price.finish(out_msg, at_sender=True)



@remaker.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message=CommandArg(), cmd: Message=RawCommand()):
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())

    name, type = linggen_get()
    result = sql_message.ramaker(name,type,user_id)
    await remaker.send(message=result,at_sender=True)


@ls_rank.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message=CommandArg(), cmd: Message=RawCommand()):
    pass

@power_rank.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message=CommandArg()):
    pass


# 重置每日签到
@scheduler.scheduled_job(
    "cron",
    hour=0,
    minute=0,
)
async def _():
    sql_message.singh_remake()
    logger.info("每日修仙签到重置成功！")


@time_mes.handle()
async def _(bot: Bot,event: GroupMessageEvent):
    global race
    group_id = await get_group_id(event.get_session_id())
    # print(event.sender.card if event.sender.card else event.sender.nickname)
    try:
        if race[group_id]:
            race_time = race[group_id].time
            time_now = datetime.now()
            if (time_now - race_time).seconds >30:
                del race[group_id]
                await time_mes.finish('太久没押注开始，被挤走了')
            else:
                pass
        else:
            pass
    except KeyError:
        pass

@remaname.handle()
async def _(bot: Bot,event: GroupMessageEvent,args: Message = CommandArg()):
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    user_name = args.extract_plain_text().strip()
    mes = sql_message.update_user_name(user_id,user_name)
    await remaname.finish(mes)


@biguan.handle()
async def _(bot: Bot, event: GroupMessageEvent,args: Message = CommandArg()):
    user_id = event.get_user_id()
    group_id = await get_group_id(event.get_session_id())
    time_biguan = args.extract_plain_text().strip()
    res = re.findall("(.*)分钟", time_biguan)
    time_t = int(res[0])
    pass



async def get_group_id(session_id):
    res = re.findall("_(.*)_", session_id)
    group_id = res[0]
    return group_id

