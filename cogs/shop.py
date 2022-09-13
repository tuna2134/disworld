from discord.ext import commands
import discord
import utils
import json

from core import Bot


class Shop(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command(name="shop")
    async def c_shop(self, ctx):
        await self.bot.lock_checker(ctx, 3)

        udata = self.bot.db.user[ctx.author.id]["Story"]
        if udata == 3:
            # チュートリアル
            await self.tutorial(ctx)
        else:
            if self.bot.version == "0.2":
                # バージョンロック
                return await ctx.send("開店準備中...")
            udata = self.bot.db.user[ctx.author.id]
            uitem = json.loads(self.bot.db.item[ctx.author.id][1])
            places = [p for p in self.bot.fielddata if p["visit"] < udata[2]]
            shops = [x for s in places for x in s["shop"]]
            msg = await ctx.send(
                embed=discord.Embed(
                    title="ショップ",
                    description="行きたいお店に行くことができます。"
                ),
                components=[utils.EasyMenu(
                    "お店を選択", 
                    "行きたいお店を選択してください。",
                    **{s["name"]:str(n) for n, s in enumerate(shops)}
                )]
            )
            inter = await msg.wait_for_dropdown(lambda i:i.author == ctx.author)
            selected = shops[int(inter.select_menu.selected_options[0].value)]
            selling_items = [self.bot.itemdata[l] for l in selected["items"]]
            embed = discord.Embed(title=selected["name"], description="買いたいアイテムを選択してください。")
            for ite in selling_items:
                if ite["type"] == "weapon":
                    embed.add_field(
                        name=ite["name"],
                        value=f"種類：武器 攻撃力：{ite['attack']} 価格：{ite['money']}")
                elif ite["type"] == "armour":
                    embed.add_field(
                        name=ite["name"],
                        value=f"種類：防具 防御力：{ite['block']} 価格：{ite['money']}")
                elif ite["type"] == "useful":
                    embed.add_field(
                        name=ite["name"],
                        value=f"種類：便利アイテム 効果：{ite['effect']} 価格：{ite['money']}")
            menu = {m["name"]:n for n, m in enumerate(selling_items)}
            await msg.edit(embed=embed, components=[menu])

            inter = await msg.wait_for_dropdown(lambda i:i.author == ctx.author)

            selected = selling_items[int(inter.select_menu.selected_options[0].value)]
            itemid = self.bot.itemdata.index(selected)
            if udata[6] < selected["money"]:
                return await ctx.edit(
                    embed=utils.ErrorEmbed("エラー", "お金が足りません。"),
                    components=[]
                )
            if not str(itemid) in uitem:
                uitem[str(itemid)] = 1
            else:
                uitem[str(itemid)] += 1
            # itemテーブルへ書き込み
            self.bot.db.item[ctx.author.id]["Data"] = json.dumps(uitem)
            udata[6] -= selected["money"]
            # moneyを減らしてusersテーブルへ書き込み
            self.bot.db.user[ctx.author.id]["Money"] = udata[6]
            await msg.edit(
                embed=discord.Embed(
                    title="成功",
                    description=f"{selected['name']}を購入しました。"
                ),
                components=[]
            )

    async def tutorial(self, ctx):
        e = discord.Embed(title="ショップ - チュートリアル", description="お店へようこそ！案内人のマスダです！\nこの街には1個のお店が存在するようですね...\nセーフィ生活店というところに行ってみましょう！")
        menu = utils.EasyMenu("お店を選択", "お店を選択してください", **{"セーフイ生活店":"1"})
        msg = await ctx.send(embed=e, components=[menu])
        await msg.wait_for_dropdown(lambda i:i.author == ctx.author)
        e = discord.Embed(title="セーフイ生活店 - チュートリアル", description="この店に来るのが初めてなので、まずはただの棒を買ってみましょう！今回だけ特別にタダで渡します！")
        menu = utils.EasyMenu("アイテムを選択", "アイテムを選択してください", **{"ただの棒":"2"})
        await msg.edit(components=[])
        msg = await ctx.send(embed=e, components=[menu])
        await msg.wait_for_dropdown(lambda i:i.author == ctx.author)
        if ctx.author.id not in self.bot.db.item:
            data = json.dumps({"0":1})
            self.bot.db.item.insert((ctx.author.id, data))
        e = discord.Embed(title="セーフイ生活店 - チュートリアル", description="しっかり商品を購入できましたね！おめでとう！\n```diff\n! ミッションクリア !\n```")
        await msg.edit(embed=e, components=[])
        self.bot.db.user[ctx.author.id]["Story"] = 4


async def setup(bot: Bot):
    await bot.add_cog(Shop(bot))