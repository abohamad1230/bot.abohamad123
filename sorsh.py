# سورس ابو حمد & خطر - النسخة النهائية
# تم التطوير لـ Render

import os
import asyncio
import re
import time
import random
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events, functions, types
from telethon.errors import FloodWaitError, ChatAdminRequiredError
from telethon.tl.types import Message
from telethon.tl.types import InputBotInlineMessageText
from telethon.tl.custom import InlineQueryResultArticle
from telethon.events import InlineQuery
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession
import yt_dlp
import requests
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "سورس ابو حمد & خطر شغال!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ===================== متغيرات البيئة =====================
API_ID = 32614186
API_HASH = '625ec61ce7182f44d4063bdb05ea3350'
MY_USER_ID = 6901525472
STRING_SESSION = '1BVtsOIYBuztdz5BuqlFDDWjQcx-StBiUkjCavqMLQKrTekWO1BmYAOyrWeQMMngjKHwyTFvCBkxBGmhAGAFK4FhYf2tN_7ECaL-7vWxpyt6g7HOZlYruzXqiu-PbzEFBfbZfoPbTA0gmf6nsnF6wDCTRZUb9lDtha-V_53wu1arAx3nIMZpAKWlrIuhtll4_XtIcc0QAOEfUw5IR3Fsn-U8AAPE8jHcXtFVAnSpCGjADRgkrAPOpVDmp12HfPX7uYD7JO8Hedzmu3YhTzklkeCngTeHxoPixMam9PZGdjf3t7HIpAmJnNbMQPx1f_auCxCeeHWE3T9uZvSRPBJ3ND6KIEm9_194='

# ===================== اعدادات السورس =====================
spam_speed = 1.0
spam_running = False
spam_task = None
spam_command = "اصمل"
spam_count = 6

insult_running = False
insult_task = None
insult_reply_id = None

extended_running = False
extended_task = None
extended_target = None

hit_running = False
hit_task = None
hit_reply_id = None

insult_list = []
extended_insult_list = []
whispered_messages = {}

MUTED_FILE = 'muted.json'
muted_users = {}
muted_tasks = {}

def load_muted():
    global muted_users
    if os.path.exists(MUTED_FILE):
        try:
            with open(MUTED_FILE, 'r', encoding='utf-8') as f:
                muted_users = json.load(f)
                print(f"تم تحميل {sum(len(users) for users in muted_users.values())} مكتم")
        except:
            muted_users = {}
    else:
        muted_users = {}

def save_muted():
    try:
        with open(MUTED_FILE, 'w', encoding='utf-8') as f:
            json.dump(muted_users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطأ في حفظ المكتمين: {e}")

load_muted()

SPAM_WORDS = [
    "يا ابن الشرموطه", "كس امك", "كس اختك", "ديوث", "هطف",
    "يا ابن المنيوكه ديوث", "قسم ب الله مسكين", "يابن الشرموطه",
    "وش فيك ديوث", "كس امك غبي", "ديوث ضعيف", "مسكين يا اخو الشرموطه",
    "ضعيف", "يابن القحبه", "ي كس امك ي فحل امك", "يا فحل امك",
    "يا كس اختك", "يابن الديوث", "يابن الخاضعه", "يابن العاهره",
    "يابن الغبيه", "يا ابن الاستقراطيه", "ي ابن العهر", "اقسم بالله اشخلك",
    "اشخل كس امك", "اختك قحبتي", "كس امك مسكين اقسم بالله", "اركب امك",
    "ياخي كس اختك", "يا ديوث", "يا فحل امك", "يا اخو الجحش",
    "يا ابن المسترخصه", "يا ابن المصخره", "ي ابن القحاب", "ي ابن الكلب",
    "يا ابن الحرام", "ي ابن الحمار", "يا ابن السرمرديه", "ي ابن الحيوانه",
    "يا ابن الغبيه", "يا ابن الوصخ", "اضرب كس امك", "ي جحش",
    "ي مسكين", "مسكين انت", "ي ابن الضعيفه", "ضعيف كس اختك",
    "يفحل امك", "يا ابن الخنزيره"
]

HIT_WORDS = [
    "اجلد كس اختك",
    "ي ابن الحيوانه",
    "تفو فكسمك",
    "ي ابن الزنوه",
    "اركب امك",
    "ي ديوث",
    "ي فحل امك",
    "ي ابن القحبه",
    "ي ابن الشرموطه",
    "ابعص امك",
    "اضرب كس اختك",
    "اضربمك",
    "يهطف",
    "يديوث",
    "يـ نياك كس امك"
]

INSULT_STORAGE = [
    "تدري ان امك من كثر ما هي مستباحة، صارت متاحة للجميع مثل خدمات الطوارئ",
    "ابوك من كثر الدياثة كاتب في بايو الفيسبوك 'البيت بيتك والمدام تحت الخدمة'",
    "امك باعت اغراض البيت عشان تشتري عطر، واخرتها ريحة الخياس غطت عليه",
    "تدري ان ابوك حاط ملصق على قفا سيارته مكتوب فيه 'ديوث وبأعلى المواصفات'",
    "دخلت الموقع لقيت امك منزلة إعلان كاتب فيه 'تخفيضات هائلة بمناسبة الويكند'",
    "اسمع يا هطف وربي لو ما تسكت لا اخلي العيال يقلبون امك موقف سيارات",
    "تدري ان امك من كثر الاستهلاك، صارت تشتغل بنظام الخدمة الذاتية للي يمرون",
    "لا تسوي فيها فحل بالقروبات يا ابن الشرموطة، انت اصلا مجرد كيس رمل للتدريب",
    "ابوك يشتغل منسق علاقات عامة عند امك، يستقبل طلبات ويرتب المواعيد",
    "تدري ان امك من كثر ما هي رخيصة، منزلة تطبيق على قوقل بلاي مجاني وبدون إعلانات",
    "ابوك فاتح مشروع استثماري ومسميه 'المدام للجميع' والربح فيه مضمون",
    "امك باعت شرفها عشان تشتري لك خط انترنت، واخرتها طالع ديوث تندعس بالقروبات",
    "تدري ان ابوك كاتب على باب بيتكم 'الدخول مجاني والمدام ترحب بكم'",
    "دخلت التليجرام لقيت امك مسوية قناة ومسميتها 'مستودع المدام' والاشتراك بريال",
    "اسمع يا هطف وربي لو ما تسكت لا اخلي الشباب يقلبون امك حلبة مصارعة",
    "تدري ان امك من كثر ما هي مستهلكة، صارت تحتاج إعادة ضبط مصنع كل أسبوع",
    "لا تسوي فيها فحل يا ابن الشرموطة، انت اصلا مجرد غلطة صارت في ممر المستشفى",
    "ابوك يشتغل حارس أمن عند امك، يفتش اللي داخلين واللي خارجين بالدور",
    "تدري ان امك من كثر ما هي مستهلكة، صارت تشتغل بنظام البصمة لعيال المنطقة",
    "ابوك مسوي قروب واتساب ومسميه 'عشاق المدام' وكل ليلة يرسل لهم الموقع",
    "امك باعت ذهبها عشان تسوي كيراتين لشعرها، واخرتها زب عابر سبيل خربه",
    "تدري ان ابوك كاتب في بايو الانستقرام 'ديوث وبكل فخر' والروابط بالستوري",
    "دخلت التيك توك لقيت امك طالعة قست مع عيال وتقول 'الي يكبس اكثر يشم'",
    "اسمع يا هطف وربي لو ما تبلع عافيتك لا اخلي الشلة يقلبون امك ساحة تفحيط",
    "تدري ان امك من كثر الخياس الي فيها، استخدموا ريحتها كسلاح بيولوجي في الحرب العالمية",
    "لا تسوي فيها صامل ومقاوم يا ابن الشرموطة، انت اصلا جاي هدية مع وجبة ماكدونالدز",
    "ابوك يشتغل سكرتير عند امك، ينظم المواعيد للي يبون ينيكونها بالدور",
    "تدري امك من كثر ما هي رخيصة مسوية اشتراك شهري لعيال الحارة",
    "ابوك من كثر الدياثة يفتح بث مباشر عشان يجمع هدايا تيك توك",
    "تدري ان امك مسجلة في الجوازات كـ 'منطقة حرة' يمر عليها الرايح والجاي بدون تصريح",
    "امك باعت شرفها عشان تشتري لك شحن العاب، واخرتها طالع ديوث وهطف ما منك فايدة",
    "دخلت السناب لقيت امك منزلة ستوري كاتب فيه 'الخاص مفتوح للجادين فقط' يا ابن الحرام",
    "اسمع يا ابن الشرموطة ورب العزة لو ما تلم نفسك لا اخلي عيال القروب يسطرونك سطر سطر",
    "تدري ان ابوك كان يوزع كروت امك كـ 'بروشورات دعاية وإعلان' في الشوارع من كرمه",
    "لا تسوي فيها هيبة يا ابن الزنوة، انت بكبرك مجرد غلطة صارت ورا مصنع الكاتشب",
    "ورب الكعبه لا اخش فحريم بيتك واحد وانيك حتى شغالتكم الوصخه",
    "قد بان خوفك واضحا في نظراتك المرتبكة وصمتك الطويل، فمن يواجهني يدرك ان الهيبة ليست كلاما يقال، بل قوة تفرض نفسها وتجعل الخصم عاجزا عن الثبات يا ابن المنيوكه",
    "طقّعه امك تركيبها الكيمائي اعقد واقوي من قنبله هيروشيما يا ابن الشرموطه",
    "حرام لا اعطى امك قرموع يسمعها ترامب ب البيت الأبيض يا ابن المنيوكه",
    "حكايتك بتصير عبره تسجل على شواهد الفشل والعار في كل مدى يا ابن المنحطه",
    "انت تائه في بحار العهر تجرك الامواج في مزاح رياح عاتيه يا ابن القحبه",
    "تبخر شرفك وبقى اسمك وصمه في سجل الاوهام والعهر والاهانه يا ابن الدنيئه",
    "انت نكته تروى على السنة الجهال في الحانات المكسوره يا ابن المنحطه",
    "صارت صورتك في المراتب تمثال فشل وعار ترمى عليه النكات يا ابن العاهره",
    "كنت كتاب فصول مزورة وشوف كيف اقلب صفحات مسيرتك البائسه امام الناس يا ابن المنحطه",
    "ما انت الا صدى ضعيف لجسد استوطنته كيانات العهر في لحظة المقياس يا ابن المنحطه فاهم كيف",
    "ابوك من كثر الدياثه مسوي 'تطبيق المدام دليفري' والتوصيل مجاني لعيال الحارة",
    "تدري إن أمك غسلت يدها من مستقبلك من يوم شافتك منزل بوست كاتب فيه 'أنا شخص غامض ولا أحد يفهمني'",
    "امك باعت ذهبها عشان تشتري لك كيبورد سريع , واخرتها طالع هطف وتندعس بكلمتين",
    "جالس تسوي فيها هيبة وتهدد، وأنت لو اختك تفتح باب غرفتك فجأة تسوي تسجيل خروج من القيم وتقفل الجوال من الخوف انها تعرف انك ديوث وممسوك ب القروبات",
    "تدري إن كرامتك منتهية لدرجة لو اختك تبي تمدحك عند الناس، تقول 'أخوي طيب بس الله يشافيه من الهطفنة'",
    "مسوي فيها راعي فزعات ولسانك طويل، وأنت لو أمك ترفع عليك المكنسة تسوي 'بلوك' لنفسك وتختفي اسبوع",
    "اسمع يا كيس البطاطس، لو ما تقفل فمك وتعدل أسلوبك، لأخلي أمك تتبرأ منك في بث مباشر وتعلن إنك غلطة مطبعية بغرفه ليله الدخله",
    "يا رجال وجهك من كثر ما هو ممسوح به البلاط، أمك صارت تستخدم صورتك بدل الفايروال عشان تطرد العين عن البيت",
    "تدري إن أمك ندمانة على كل ريال دفعته في تربيتك، من يوم شافتك جالس بآخر الليل تتهزأ من عيال التلي ودمعتك على خدك",
    "جالس تتفلسف وتهايط، وأمك المسكينة تحسب إنك قاعد تدرس للمستقبل، وهي ما تدري إنك صاير جدار حماية يندعس عليه بالرايح والجاي",
    "أمك باعت ذهبها عشان تجيب لك جهاز تدير فيه مستقبلك، وآخرتها طالع هطف ومنبطح في كل التلي وما فالح إلا تصيح بالخاص ونمص كسمك",
]

INSULT_WITH_NAME = [
    "يا {name} تدري ان طقعه امك تركيبها الكيميائي اعقد من لغز مثلث برمودا",
    "تدري يا {name} يا منبطح الصالة ان امك من كثر الرخص، منزلة تحديث جديد يوفر ميزة 'التوصيل السريع للمنازل'",
    "يا {name} ابوك من كثر ما هو فاقد الأمل فيك، صار يوزع كروت اختك مع كيس الخبز كدعاية للمحل الجديد",
    "يا {name} امك كانت معي بالسيارة قلت لها عطيني سطر قوي، طالعت فيني وقالت 'صب صب شطة لا يبرد السندويش'",
    "تدري يا {name} ان اختك مسجلة في قوقل ماب كـ 'مرفق عام مفتوح للجميع' والتقييم حقها نجمة واحدة من الخياس",
    "يا {name} اللهم لا سهل إلا ما جعلته سهلاً، انا راح اطب بكرامة حريم بيتك وإن شاء الله التفتيش يكون سريع",
    "يا {name} ابوك من كثر الدياثة كاتب في بايو الانستقرام 'البيت بيتك والمدام تحت الخدمة.. والروابط بالستوري'",
    "مرة دخلت السناب لقيت اختك يا {name} منزلة ستوري كاتب فيه 'الخاص مفتوح لعيال القروب والتحويل بعد الخدمة'",
    "يا {name} امك باعت غسالة الصحون عشان تشحن لك باقة 'المنبطح المعتمد' واخرتها طالع هطف تندعس بغرفتك",
    "اسمع يا {name} يا ابن الشرموطة ورب العزة لو ما تلم نفسك لا اخلي عيال الشات يسطرون هيبتك سطر سطر",
    "يا {name} قد بان خوفك واضحاً في نظراتك المرتبكة وصمتك الطويل، ابلع الموس وانكتم قدام أسيادك يا هطف",
    "حرام يا {name} لا اعطي امك قرموع يسمع صياحها بايدن في أمريكا ويطلع بيان استنكار دولي عاجل",
    "يا {name} انت بكبرك مجرد غلطة مصنعية صارت ورا المستودع القديم، وبقى اسمك وصمة عار بين المنبطحين",
    "صارت صورتك يا {name} في القروبات تمثال للفشل، والعيال يطقطقون عليك وأنت تنتظر سندويش الجبن من الوالدة",
    "ما انت يا {name} إلا كيس رمل للتدريب، نجلد فيك طول اليوم وأنت تسلك وتقول 'أصلاً عادي' يا ابن المنحطة",
    "تدري يا {name} يا منبطح الصالة ان امك من كثر الرخص، نزلوا لها تطبيق بالـ 'جوجل بلاي' مجاني ومصنف كـ 'مرفق عام عالي الاستهلاك'",
    "يا {name} ابوك من كثر ما هو غاسل يده من مرجلتك الضائعة، صار يوزع كروت اختك مع الفواكه كدعاية وتشجيع لعيال الحارة",
    "يا {name} امك كانت معي بالسيارة قلت لها عطيني سطر يفجر كرامة ولدك، طالعت فيني ببرود وقالت 'المهم الجبن المراعي ولا بوك؟'",
    "تدري يا {name} ان اختك مسجلة في قوقل ماب كـ 'ساحة عامة للخدمات السريعة والمجانية' والتقييم تحت الصفر بسبب سوء الخدمة والخياس",
    "يا {name} اللهم لا سهل إلا ما جعلته سهلاً، انا راح اطب بكرامة حريم بيتك واحد واحد، وإن شاء الله الجلد يكون سريع وممتع للقروب",
    "يا {name} تدري ان طقعة امك تركيبها الكيميائي اعقد من مفاعل نووي مصدي.. ريحتها خلت بعارين الحارة تطلب لجوء سياسي لكندا",
    "يا {name} ابوك من كثر الدياثة كاتب في بايو السناب 'البيت مفتوح والمدام جاهزة.. والموقع لعيال سورس خطر بالخاص مع قهوة مجانية'",
    "مرة دخلت الانستقرام لقيت اختك يا {name} منزلة بوست كاتب فيه 'الدايركت مفتوح للجادين والدفع بالآجل بعد انتهاء الخدمة للمنبطحين'",
    "يا {name} امك باعت لمبة غرفتك عشان تشحن لك إنترنت، وأخرتها طالع ديوث وهطف وقاعد بالظلام تندعس وتطالب بفزعة وهمية",
    "اسمع يا {name} يا ابن الشرموطة ورب العزة لو ما تنكتم لا اخلي عيال الشات يقلبون هيبتك تشليح سكراب وسوالف يطقطقون عليها سطر سطر",
    "يا {name} قد بان خوفك واضحاً في كتابتك البطيئة وصمتك الطويل، ابلع الموس وانكتم قدام أسيادك يا منبطح لغرفة الجبن",
    "حرام يا {name} لا اعطي امك قرموع يسمع صياحها رئيس مجلس الأمن الدولي ويطلع قرار حظر تجول دولي وعقوبات صارمة في بيتكم",
    "يا {name} انت بكبرك مجرد غلطة مصنعية صارت ورا التانكي القديم، وبقى اسمك وصمة عار وسالفة يضحكون عليها العيال بالصوتيات",
    "صارت صورتك يا {name} في القروبات تمثال للانبطاح المعتمد، والشباب يطقطقون عليك وأنت تنتظر امك تجيب لك السندويش لغرفتك وأنت منجلد",
    "ما انت يا {name} إلا حبة بندول منتهية الصلاحية، نجلد فيك طول السهرة ونمسح فيك البلاط وأنت تسلك وتقول 'أصلاً عادي' يا ابن المنحطة",
]

class AntiRepeat:
    def __init__(self, repeat_limit=10):
        self.repeat_limit = repeat_limit
        self.message_count = 0
        self.sent_messages = []
        self.current_index = 0
        self.shuffled_list = []
        self.last_10_messages = []
        
    def shuffle_list(self, insult_list):
        self.shuffled_list = insult_list.copy()
        random.shuffle(self.shuffled_list)
        self.current_index = 0
        self.sent_messages.clear()
        self.last_10_messages.clear()
        self.message_count = 0
        
    def get_next_message(self, insult_list, name=None):
        if not insult_list:
            return None
            
        if not self.shuffled_list or self.current_index >= len(self.shuffled_list):
            self.shuffle_list(insult_list)
            
        if self.current_index < len(self.shuffled_list):
            message = self.shuffled_list[self.current_index]
            self.current_index += 1
            
            if name and '{name}' in message:
                message = message.replace('{name}', name)
                
            self.last_10_messages.append(message)
            if len(self.last_10_messages) > 10:
                self.last_10_messages.pop(0)
                
            self.message_count += 1
            return message
            
        self.shuffle_list(insult_list)
        return self.get_next_message(insult_list, name)

anti_repeat = AntiRepeat(repeat_limit=10)

# ===================== تعريف الـ Client =====================
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ===================== دوال تحميل يوتيوب وتيك توك =====================
async def download_youtube_audio(query):
    try:
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1',
            'noplaylist': True,
            'ignoreerrors': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if info and 'entries' in info:
                video = info['entries'][0]
                if video:
                    ydl_opts_download = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'outtmpl': 'downloads/%(title)s.%(ext)s',
                        'quiet': True,
                        'no_warnings': True,
                        'noplaylist': True,
                        'ignoreerrors': True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_download:
                        ydl_download.download([video['webpage_url']])
                        filename = ydl_download.prepare_filename(video)
                        mp3_file = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                        if os.path.exists(mp3_file):
                            return mp3_file
                        else:
                            for f in os.listdir('downloads'):
                                if f.endswith('.mp3'):
                                    return os.path.join('downloads', f)
        return None
    except Exception as e:
        print(f"خطأ في تحميل يوتيوب: {e}")
        return None

async def download_tiktok_video(url):
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data'):
                video_url = data['data'].get('play')
                if video_url:
                    video_response = requests.get(video_url, headers=headers)
                    if video_response.status_code == 200:
                        filename = f"tiktok_{random.randint(1000,9999)}.mp4"
                        with open(filename, 'wb') as f:
                            f.write(video_response.content)
                        return filename
        return None
    except Exception as e:
        print(f"خطأ في تحميل تيك توك: {e}")
        return None

# ===================== دوال مساعدة =====================
async def send_to_saved_messages(text):
    try:
        await client.send_message('me', text)
    except Exception as e:
        print(f"خطأ في إرسال للرسائل المحفوظة: {e}")

async def get_sender_name(event):
    if event.sender_id:
        try:
            sender = await client.get_entity(event.sender_id)
            return sender.first_name or sender.username or str(sender.id)
        except:
            return str(event.sender_id)
    return "مستخدم"

async def mute_user_permanently(chat_id, user_id):
    try:
        if str(chat_id) not in muted_users:
            muted_users[str(chat_id)] = {}
        muted_users[str(chat_id)][str(user_id)] = True
        save_muted()
        return True
    except Exception as e:
        print(f"خطأ في كتم المستخدم: {e}")
        return False

async def unmute_user_permanently(chat_id, user_id):
    try:
        if str(chat_id) in muted_users and str(user_id) in muted_users[str(chat_id)]:
            del muted_users[str(chat_id)][str(user_id)]
            save_muted()
        return True
    except Exception as e:
        print(f"خطأ في فك الكتم: {e}")
        return False

def generate_random_spam_line(count=6):
    if count > len(SPAM_WORDS):
        count = len(SPAM_WORDS)
    shuffled_words = SPAM_WORDS.copy()
    random.shuffle(shuffled_words)
    selected_words = shuffled_words[:count]
    random.shuffle(selected_words)
    return " ".join(selected_words)

def get_random_hit_line():
    return random.choice(HIT_WORDS)

async def insult_loop_reply(chat_id, speed, reply_to_id, target_id):
    global insult_running
    count = 1
    while insult_running:
        try:
            insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
            if not insult_text:
                anti_repeat.shuffle_list(INSULT_STORAGE)
                insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
            if insult_text:
                await client.send_message(chat_id, insult_text, reply_to=reply_to_id)
                count += 1
            await asyncio.sleep(speed)
        except Exception as e:
            print(f"خطأ في نيك ام المستمر مع الرد: {e}")
            await asyncio.sleep(1)

async def hit_loop_reply(chat_id, speed, reply_to_id, target_id):
    global hit_running
    count = 1
    while hit_running:
        try:
            hit_line = get_random_hit_line()
            await client.send_message(chat_id, hit_line, reply_to=reply_to_id)
            count += 1
            await asyncio.sleep(speed)
        except Exception as e:
            print(f"خطأ في اضربه المستمر مع الرد: {e}")
            await asyncio.sleep(1)

async def random_spam_loop_reply(chat_id, speed, reply_to_id):
    global spam_running
    count_num = 1
    while spam_running:
        try:
            spam_line = generate_random_spam_line(spam_count)
            await client.send_message(chat_id, spam_line, reply_to=reply_to_id)
            await asyncio.sleep(speed)
            count_num += 1
            if count_num % 30 == 0:
                await send_to_saved_messages(f"التسطير مستمر... ({count_num} سطر)")
        except Exception as e:
            print(f"خطأ في التسطير العشوائي مع الرد: {e}")
            await asyncio.sleep(1)

async def random_spam_loop(chat_id, speed):
    global spam_running
    count_num = 1
    while spam_running:
        try:
            spam_line = generate_random_spam_line(spam_count)
            await client.send_message(chat_id, spam_line)
            await asyncio.sleep(speed)
            count_num += 1
            if count_num % 30 == 0:
                await send_to_saved_messages(f"التسطير مستمر... ({count_num} سطر)")
        except Exception as e:
            print(f"خطأ في التسطير العشوائي: {e}")
            await asyncio.sleep(1)

# ===================== امر تحميل يوتيوب =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^يوت\s+(.+)$'))
async def youtube_search(event):
    try:
        query = event.pattern_match.group(1).strip()
        if not query:
            await event.edit("اكتب اسم الاغنيه او المقطع")
            return
        
        await event.edit("جاري البحث عن المقطع وتحميله... يرجى الانتظار")
        
        audio_file = await download_youtube_audio(query)
        if audio_file and os.path.exists(audio_file):
            await client.send_file(event.chat_id, audio_file, caption="تم التحميل من يوتيوب")
            try:
                os.remove(audio_file)
            except:
                pass
            await event.delete()
        else:
            await event.edit("فشل التحميل، حاول مرة ثانية او تأكد من اسم الاغنيه")
    except Exception as e:
        await event.edit(f"خطأ: {str(e)[:50]}")

# ===================== امر تحميل تيك توك =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^تحميل تيك\s+(https?://[^\s]+)$'))
async def download_tiktok(event):
    try:
        url = event.pattern_match.group(1)
        await event.edit("جاري تحميل المقطع من تيك توك...")
        
        video_file = await download_tiktok_video(url)
        if video_file and os.path.exists(video_file):
            await client.send_file(event.chat_id, video_file, caption="تم التحميل من تيك توك (بدون علامه مائيه)")
            os.remove(video_file)
            await event.delete()
        else:
            await event.edit("فشل التحميل، حاول مرة ثانية")
    except Exception as e:
        await event.edit(f"خطأ: {str(e)[:50]}")

# ===================== امر تحويل الميديا المؤقته =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^تحويل$'))
async def convert_media(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("الرجاء الرد على صوره او فيديو او صوتيه مؤقته")
            return
        
        if reply.photo:
            try:
                photo_path = await client.download_media(reply.photo, file="temp_media.jpg")
                if photo_path:
                    await client.send_file('me', photo_path, caption="تم تحويل الصوره المؤقته")
                    try:
                        os.remove(photo_path)
                    except:
                        pass
                    await event.edit("تم تحويل الصوره المؤقته وحفظها في الرسائل المحفوظه")
                else:
                    await event.edit("فشل تحميل الصوره")
            except Exception as e:
                await event.edit(f"خطأ: {str(e)[:50]}")
        
        elif reply.video:
            try:
                video_path = await client.download_media(reply.video, file="temp_video.mp4")
                if video_path:
                    await client.send_file('me', video_path, caption="تم تحويل الفيديو المؤقت")
                    try:
                        os.remove(video_path)
                    except:
                        pass
                    await event.edit("تم تحويل الفيديو المؤقت وحفظه في الرسائل المحفوظه")
                else:
                    await event.edit("فشل تحميل الفيديو")
            except Exception as e:
                await event.edit(f"خطأ: {str(e)[:50]}")
        
        elif reply.voice:
            try:
                voice_path = await client.download_media(reply.voice, file="temp_voice.mp3")
                if voice_path:
                    await client.send_file('me', voice_path, caption="تم تحويل الصوتيه المؤقته")
                    try:
                        os.remove(voice_path)
                    except:
                        pass
                    await event.edit("تم تحويل الصوتيه المؤقته وحفظها في الرسائل المحفوظه")
                else:
                    await event.edit("فشل تحميل الصوتيه")
            except Exception as e:
                await event.edit(f"خطأ: {str(e)[:50]}")
        
        elif reply.document:
            try:
                file_path = await client.download_media(reply.document, file="temp_file")
                if file_path:
                    await client.send_file('me', file_path, caption="تم تحويل الملف المؤقت")
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    await event.edit("تم تحويل الملف المؤقت وحفظه في الرسائل المحفوظه")
                else:
                    await event.edit("فشل تحميل الملف")
            except Exception as e:
                await event.edit(f"خطأ: {str(e)[:50]}")
        else:
            await event.edit("الرجاء الرد على صوره او فيديو او صوتيه مؤقته")
            
    except Exception as e:
        await event.edit(f"خطأ: {str(e)[:50]}")

# ===================== امر حذف رسايلي =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^حذف رسايلي$'))
async def delete_my_messages(event):
    try:
        await event.delete()
        await send_to_saved_messages("جاري حذف آخر 1000 رسالة من المحادثة...")
        
        chat_id = event.chat_id
        deleted_count = 0
        
        try:
            async for msg in client.iter_messages(chat_id, from_user='me', limit=1000):
                try:
                    await client.delete_messages(chat_id, msg.id)
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"خطأ في حذف رسالة: {e}")
                    continue
        except Exception as e:
            print(f"خطأ في جلب الرسائل: {e}")
        
        await send_to_saved_messages(f"تم حذف {deleted_count} رسالة بنجاح من المحادثة!")
        
    except Exception as e:
        await send_to_saved_messages(f"خطأ في حذف الرسائل: {str(e)}")

# ===================== مراقب حذف رسائل المكتمين =====================
@client.on(events.NewMessage)
async def delete_muted_messages(event):
    if event.out:
        return
    
    chat_id = event.chat_id
    sender_id = event.sender_id
    
    if str(chat_id) in muted_users and str(sender_id) in muted_users[str(chat_id)]:
        try:
            await client.delete_messages(chat_id, event.id)
            print(f"تم حذف رسالة من مكتم {sender_id} في الشات {chat_id}")
        except Exception as e:
            print(f"خطأ في حذف رسالة مكتم: {e}")

# ===================== اوامر التسطير =====================
@client.on(events.NewMessage(outgoing=True))
async def dynamic_spam_handler(event):
    global spam_running, spam_task, spam_speed, spam_command, spam_count
    
    if not event.text:
        return
        
    match = re.match(r'^' + re.escape(spam_command) + r'\s+(\d+)$', event.text)
    if match:
        count = int(match.group(1))
        if 1 <= count <= 20:
            spam_count = count
            await event.edit(f"تم ضبط عدد الكلمات إلى {count}")
            await send_to_saved_messages(f"تم ضبط عدد الكلمات في التسطير إلى {count}")
            return
    
    if event.text == spam_command:
        if spam_running:
            await send_to_saved_messages("التسطير يعمل بالفعل!")
            return
            
        try:
            spam_running = True
            await send_to_saved_messages(f"تم بدء التسطير العشوائي!\nالسرعة: {spam_speed} ثانية\nعدد الكلمات: {spam_count}")
            spam_task = asyncio.create_task(random_spam_loop(event.chat_id, spam_speed))
        except Exception as e:
            await send_to_saved_messages(f"خطأ في التسطير: {e}")
        return
    
    if event.text == spam_command and event.is_reply:
        try:
            reply = await event.get_reply_message()
            if reply:
                if spam_running:
                    await send_to_saved_messages("التسطير يعمل بالفعل!")
                    return
                
                spam_running = True
                await send_to_saved_messages(f"تم بدء التسطير العشوائي مع الرد!\nالسرعة: {spam_speed} ثانية\nعدد الكلمات: {spam_count}")
                spam_task = asyncio.create_task(random_spam_loop_reply(event.chat_id, spam_speed, reply.id))
        except Exception as e:
            await send_to_saved_messages(f"خطأ في التسطير بالرد: {e}")
        return

# ===================== اوامر نيك ام =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^نيك ام$'))
async def insult_mom(event):
    global insult_running, insult_task, insult_reply_id
    
    try:
        reply = await event.get_reply_message()
        
        if not reply:
            await event.delete()
            await send_to_saved_messages("تم تنفيذ امر نيك ام (بدون رد)")
            return
        
        if insult_running:
            await event.delete()
            await send_to_saved_messages("نيك ام يعمل بالفعل!")
            return
        
        await event.delete()
        insult_running = True
        insult_reply_id = reply.id
        
        await send_to_saved_messages(f"تم بدء نيك ام المستمر مع الرد على رسالة {reply.sender_id}\nالسرعة: {spam_speed} ثانية")
        
        insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
        if not insult_text:
            anti_repeat.shuffle_list(INSULT_STORAGE)
            insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
        if insult_text:
            await client.send_message(event.chat_id, insult_text, reply_to=reply.id)
        
        insult_task = asyncio.create_task(insult_loop_reply(event.chat_id, spam_speed, reply.id, reply.sender_id))
        
    except Exception as e:
        await send_to_saved_messages(f"خطأ في نيك ام: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^نيك ام (.+)$'))
async def insult_with_name(event):
    global insult_running, insult_task, insult_reply_id
    
    try:
        name = event.pattern_match.group(1).strip()
        reply = await event.get_reply_message()
        
        if not reply:
            await event.delete()
            await send_to_saved_messages(f"تم تنفيذ امر نيك ام على {name} (بدون رد)")
            return
        
        if insult_running:
            await event.delete()
            await send_to_saved_messages("نيك ام يعمل بالفعل!")
            return
        
        await event.delete()
        insult_running = True
        insult_reply_id = reply.id
        
        if name.startswith('@'):
            try:
                entity = await client.get_entity(name)
                name = entity.first_name or name
            except:
                pass
        
        await send_to_saved_messages(f"تم بدء نيك ام المستمر على {name} مع الرد على رسالته\nالسرعة: {spam_speed} ثانية")
        
        insult_text = anti_repeat.get_next_message(INSULT_WITH_NAME, name)
        if not insult_text:
            anti_repeat.shuffle_list(INSULT_WITH_NAME)
            insult_text = anti_repeat.get_next_message(INSULT_WITH_NAME, name)
        if insult_text:
            await client.send_message(event.chat_id, insult_text, reply_to=reply.id)
        
        insult_task = asyncio.create_task(insult_loop_reply(event.chat_id, spam_speed, reply.id, reply.sender_id))
            
    except Exception as e:
        await send_to_saved_messages(f"خطأ في نيك ام باسم: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^وقف نيك امه$'))
async def stop_insult(event):
    global insult_running, insult_task
    try:
        await event.edit("بوقف نيك فكسمه المخيس")
        if insult_running:
            insult_running = False
            if insult_task:
                insult_task.cancel()
            await send_to_saved_messages("تم توقيف نيك ام")
        else:
            await send_to_saved_messages("نيك ام غير مفعل")
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

# ===================== امر بعص امه =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^بعص امه$'))
async def extended_insult(event):
    global extended_running, extended_task, extended_target
    
    try:
        reply = await event.get_reply_message()
        
        if not reply:
            await event.delete()
            await send_to_saved_messages("تم تنفيذ امر بعص امه (بدون رد)")
            return
        
        if extended_running:
            await event.delete()
            await send_to_saved_messages("بعص امه يعمل بالفعل!")
            return
        
        await event.delete()
        extended_running = True
        extended_target = reply.sender_id
        
        sender_name = await get_sender_name(reply)
        await send_to_saved_messages(f"تم بدء بعص امه المستمر على {sender_name}\nالسرعة: {spam_speed} ثانية")
        
        insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
        if not insult_text:
            anti_repeat.shuffle_list(INSULT_STORAGE)
            insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
        if insult_text:
            await client.send_message(event.chat_id, insult_text, reply_to=reply.id)
        
        @client.on(events.NewMessage(from_users=reply.sender_id))
        async def reply_to_target(target_event):
            if extended_running:
                insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
                if not insult_text:
                    anti_repeat.shuffle_list(INSULT_STORAGE)
                    insult_text = anti_repeat.get_next_message(INSULT_STORAGE)
                if insult_text:
                    try:
                        await client.send_message(target_event.chat_id, insult_text, reply_to=target_event.id)
                    except:
                        pass
        
        extended_task = asyncio.create_task(asyncio.sleep(0))
        
    except Exception as e:
        await send_to_saved_messages(f"خطأ في بعص امه: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^وقف بعص امه$'))
async def stop_extended(event):
    global extended_running, extended_task
    try:
        await event.edit("ب اوقف بعص فكسمه المخمج")
        if extended_running:
            extended_running = False
            if extended_task:
                extended_task.cancel()
            await send_to_saved_messages("تم توقيف بعص امه")
        else:
            await send_to_saved_messages("بعص امه غير مفعل")
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

# ===================== امر اضربه =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^اضربه$'))
async def hit_command(event):
    global hit_running, hit_task, hit_reply_id
    
    try:
        reply = await event.get_reply_message()
        
        if not reply:
            if hit_running:
                await event.edit("اضربه يعمل بالفعل!")
                return
            
            await event.edit("ب اضرب امه")
            hit_running = True
            await send_to_saved_messages(f"تم بدء الضرب المستمر في الشات!\nالسرعة: {spam_speed} ثانية")
            hit_task = asyncio.create_task(hit_loop_reply(event.chat_id, spam_speed, None, None))
            return
        
        if hit_running:
            await event.edit("اضربه يعمل بالفعل!")
            return
        
        await event.edit("ب اضرب امه")
        hit_running = True
        hit_reply_id = reply.id
        
        sender_name = await get_sender_name(reply)
        await send_to_saved_messages(f"تم بدء الضرب المستمر على {sender_name} مع الرد على رسالته\nالسرعة: {spam_speed} ثانية")
        
        hit_line = get_random_hit_line()
        await client.send_message(event.chat_id, hit_line, reply_to=reply.id)
        
        hit_task = asyncio.create_task(hit_loop_reply(event.chat_id, spam_speed, reply.id, reply.sender_id))
                
    except Exception as e:
        await send_to_saved_messages(f"خطأ في اضربه: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^وقف ضرب$'))
async def stop_hit(event):
    global hit_running, hit_task
    try:
        await event.delete()
        if hit_running:
            hit_running = False
            if hit_task:
                hit_task.cancel()
            await send_to_saved_messages("تم توقيف الضرب")
        else:
            await send_to_saved_messages("الضرب غير مفعل")
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

# ===================== امر وقف الكل =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^وقف الكل$'))
async def stop_all(event):
    global insult_running, extended_running, hit_running, spam_running
    global insult_task, extended_task, hit_task, spam_task
    
    try:
        await event.delete()
        stopped = []
        
        if insult_running:
            insult_running = False
            if insult_task:
                insult_task.cancel()
            stopped.append("نيك ام")
        
        if extended_running:
            extended_running = False
            if extended_task:
                extended_task.cancel()
            stopped.append("بعص امه")
        
        if hit_running:
            hit_running = False
            if hit_task:
                hit_task.cancel()
            stopped.append("ضرب")
        
        if spam_running:
            spam_running = False
            if spam_task:
                spam_task.cancel()
            stopped.append("تسطير")
        
        if stopped:
            await send_to_saved_messages(f"تم ايقاف جميع الهجمات\n({', '.join(stopped)})")
        else:
            await send_to_saved_messages("لا توجد هجمات مفعلة")
            
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

# ===================== اوامر السرعة =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^السرعة\s+(\d+\.?\d*)$'))
async def set_speed(event):
    global spam_speed
    try:
        speed = float(event.pattern_match.group(1))
        if speed < 0.1:
            await event.edit("السرعة الأقل هي 0.1 ثانية")
            return
        if speed > 10:
            await event.edit("السرعة الأقصى هي 10 ثواني")
            return
        spam_speed = speed
        await event.edit(f"تم ضبط السرعة إلى {spam_speed} ثانية")
        await send_to_saved_messages(f"تم ضبط السرعة إلى {spam_speed} ثانية")
    except:
        await event.edit("استخدم: السرعة <رقم> (0.1 ~ 10)")

@client.on(events.NewMessage(outgoing=True, pattern=r'^وقف جلد$'))
async def stop_spam(event):
    global spam_running, spam_task
    try:
        await event.delete()
        if spam_running:
            spam_running = False
            if spam_task:
                spam_task.cancel()
            await send_to_saved_messages("تم توقيف الجلد")
        else:
            await send_to_saved_messages("الجلد غير مفعل")
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

# ===================== اوامر الكتم =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^اخرس$'))
async def mute_user_with_delete(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await send_to_saved_messages("يرجى الرد على شخص لكتمه!")
            return
        
        user_id = reply.sender_id
        sender_name = await get_sender_name(reply)
        
        success = await mute_user_permanently(event.chat_id, user_id)
        
        if success:
            await send_to_saved_messages(f"تم كتم {sender_name} في هذا الشات (سيتم حذف رسائله الجديدة)")
        else:
            await send_to_saved_messages(f"فشل كتم {sender_name}")
            
    except Exception as e:
        await send_to_saved_messages(f"خطأ في كتم العضو: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اخرسس$'))
async def mute_user_with_insult(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("يرجى الرد على شخص لكتمه!")
            return
        
        await event.edit("اخرسسس ي ابن القحبه")
        
        user_id = reply.sender_id
        sender_name = await get_sender_name(reply)
        
        success = await mute_user_permanently(event.chat_id, user_id)
        
        if success:
            await send_to_saved_messages(f"تم كتم {sender_name} في هذا الشات (سيتم حذف رسائله الجديدة)")
        else:
            await send_to_saved_messages(f"فشل كتم {sender_name}")
            
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^اخرسو$'))
async def mute_all_members(event):
    try:
        await event.delete()
        await send_to_saved_messages("جاري كتم جميع الأعضاء...")
        
        participants = await client.get_participants(event.chat_id)
        muted_count = 0
        
        for user in participants:
            if user.bot or user.deleted or user.id == client.get_me().id:
                continue
            try:
                success = await mute_user_permanently(event.chat_id, user.id)
                if success:
                    muted_count += 1
                await asyncio.sleep(0.3)
            except:
                continue
        
        await send_to_saved_messages(f"تم كتم {muted_count} عضو في هذا الشات")
        
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

# ===================== اوامر فك الكتم =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^تنفس$'))
async def unmute_user_breath(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await send_to_saved_messages("يرجى الرد على شخص لفك كتمه!")
            return
        
        user_id = reply.sender_id
        sender_name = await get_sender_name(reply)
        
        success = await unmute_user_permanently(event.chat_id, user_id)
        
        if success:
            await send_to_saved_messages(f"تم فك كتم {sender_name} في هذا الشات")
        else:
            await send_to_saved_messages(f"فشل فك كتم {sender_name}")
            
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^تكلم يا ابن الزنوه$'))
async def unmute_user_with_insult(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await send_to_saved_messages("يرجى الرد على شخص لفك كتمه!")
            return
        
        user_id = reply.sender_id
        sender_name = await get_sender_name(reply)
        
        success = await unmute_user_permanently(event.chat_id, user_id)
        
        if success:
            await send_to_saved_messages(f"تم فك كتم {sender_name} في هذا الشات")
        else:
            await send_to_saved_messages(f"فشل فك كتم {sender_name}")
            
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^فك كتم الكل$'))
async def unmute_all_members(event):
    try:
        await event.delete()
        await send_to_saved_messages("جاري فك كتم جميع الأعضاء...")
        
        if str(event.chat_id) in muted_users:
            count = len(muted_users[str(event.chat_id)])
            muted_users[str(event.chat_id)] = {}
            save_muted()
            await send_to_saved_messages(f"تم فك كتم {count} عضو في هذا الشات")
        else:
            await send_to_saved_messages("لا يوجد مكتمين في هذا الشات")
        
    except Exception as e:
        await send_to_saved_messages(f"خطأ: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r'^قائمه الكتم$'))
async def show_muted(event):
    try:
        if not muted_users:
            await event.edit("لا يوجد مكتمين")
            return
        
        result = "قائمة المكتمين:\n"
        for chat_id, users in muted_users.items():
            try:
                chat = await client.get_entity(int(chat_id))
                chat_name = chat.title if hasattr(chat, 'title') else "خاص"
            except:
                chat_name = str(chat_id)
            
            result += f"\n{chat_name}:\n"
            for user_id in users:
                try:
                    user = await client.get_entity(int(user_id))
                    name = f"@{user.username}" if user.username else user.first_name
                except:
                    name = str(user_id)
                result += f"  {name}\n"
        
        await event.edit(result)
        
    except Exception as e:
        await event.edit(f"خطأ: {e}")

# ===================== امر كشف الهمسه =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^كشف الهمسه$'))
async def reveal_whisper(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("يرجى الرد على رسالة الهمس!")
            return
        
        if reply.text.startswith('/whisper') or 'whisper' in reply.text.lower():
            whisper_content = reply.text.replace('/whisper', '').strip()
            if not whisper_content:
                whisper_content = "رسالة همس فارغة"
            
            await event.edit(f"محتوى الهمس:\n{whisper_content}")
        else:
            await event.edit("هذه ليست رسالة همس!")
    except Exception as e:
        await event.respond(f"خطأ: {e}")

# ===================== امر اذاعه =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^أذاعه$'))
async def broadcast_reply(event):
    try:
        reply = await event.get_reply_message()
        if not reply:
            await event.edit("يرجى الرد على رسالة للاذاعه!")
            return
        
        await event.edit("جاري ارسال الاذاعه...")
        
        dialogs = await client.get_dialogs()
        sent_count = 0
        
        for dialog in dialogs:
            try:
                if dialog.is_user or dialog.is_group or dialog.is_channel:
                    await client.forward_messages(dialog.id, [reply])
                    sent_count += 1
                    await asyncio.sleep(0.5)
            except:
                continue
            
            if sent_count >= 100:
                break
        
        await event.edit(f"تم ارسال الاذاعه لـ {sent_count} جهه!")
        await send_to_saved_messages(f"تم ارسال الاذاعه لـ {sent_count} جهه")
    except Exception as e:
        await event.respond(f"خطأ: {e}")

# ===================== امر تفليش القروب =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^تفليش القروب$'))
async def flush_group(event):
    try:
        await event.edit("جاري تفليش القروب...")
        
        participants = await client.get_participants(event.chat_id)
        kicked_count = 0
        
        for user in participants:
            if user.bot or user.deleted or user.id == client.get_me().id:
                continue
            try:
                await client(functions.channels.EditBannedRequest(
                    channel=event.chat_id,
                    participant=user.id,
                    banned_rights=types.ChatBannedRights(
                        until_date=datetime.now() + timedelta(days=1),
                        view_messages=True
                    )
                ))
                kicked_count += 1
                await asyncio.sleep(0.5)
            except:
                continue
        
        await event.edit(f"تم طرد {kicked_count} عضو بنجاح!")
        await send_to_saved_messages(f"تم طرد {kicked_count} عضو من القروب")
    except Exception as e:
        await event.respond(f"فشل التفليش: {str(e)}")

# ===================== امر تغيير امر التسطير =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^تغيير امر التسطير (.+)$'))
async def change_spam_command(event):
    global spam_command
    try:
        new_command = event.pattern_match.group(1).strip()
        old_command = spam_command
        spam_command = new_command
        await event.edit(f"تم تغيير امر التسطير!\nالقديم: {old_command}\nالجديد: {new_command}")
        await send_to_saved_messages(f"تم تغيير امر التسطير إلى {new_command}")
    except Exception as e:
        await event.respond(f"خطأ: {e}")

# ===================== امر ضبط عدد الكلمات =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^عدد الكلمات (\d+)$'))
async def set_spam_count(event):
    global spam_count
    try:
        count = int(event.pattern_match.group(1))
        if count < 1 or count > 20:
            await event.edit("العدد المسموح من 1 إلى 20")
            return
        spam_count = count
        await event.edit(f"تم ضبط عدد الكلمات إلى {count}")
        await send_to_saved_messages(f"تم ضبط عدد الكلمات إلى {count}")
    except Exception as e:
        await event.edit(f"خطأ: {e}")

# ===================== امر قائمة السطور =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^قائمة السطور$'))
async def show_lines_list(event):
    try:
        total_insults = len(INSULT_STORAGE) + len(INSULT_WITH_NAME)
        total_spam = len(SPAM_WORDS)
        total_hit = len(HIT_WORDS)
        total_insult_list = len(insult_list) + len(extended_insult_list)
        
        response = f"احصائيات السطور:\n\n"
        response += f"سطور نيك ام: {len(INSULT_STORAGE)}\n"
        response += f"سطور مع اسم: {len(INSULT_WITH_NAME)}\n"
        response += f"سطور التسطير: {total_spam}\n"
        response += f"سطور اضربه: {total_hit}\n"
        response += f"سطور مزروفة: {total_insult_list}\n"
        response += f"المجموع الكلي: {total_insults + total_spam + total_hit + total_insult_list}\n\n"
        response += f"نظام منع التكرار: مفعل (اخر 10 سطور)\n"
        response += f"امر التسطير الحالي: {spam_command}\n"
        response += f"عدد الكلمات: {spam_count}\n"
        response += f"السرعة الحالية: {spam_speed} ثانية\n"
        
        await event.edit(response)
        
    except Exception as e:
        await event.respond(f"خطأ: {e}")

# ===================== امر المساعدة (قائمة الاوامر) =====================
@client.on(events.NewMessage(outgoing=True, pattern=r'^الاوامر$'))
async def help_command(event):
    help_text = """
Welcome ~ قائمة أوامر سورس ابو حمد & خطر


أوامر التسطير
━━━━━━━━━━━━━━━━━━━━━━━━━

اصمل - يقعد يسطر (بدون رد)
اصمل مع ريبلاي - يقعد يسطره مع رد على نفس الرسالة

تغيير امر التسطير <الامر الجديد>  يعني الحين تبي تسطر بدون لا احد يكشفك يمديك تغيير امر التسطير كل شوي   وعشان تغيره تكتب < تغيير امر التسطير كس اختك > 
الحين لو كتبت كس اختك ب يقعد يسطر بدال الامر القديم الي هو اصمل  


عدد الكلمات <رقم> - ضبط عدد الكلمات (1-20)
وقف جلد - إيقاف التسطير
السرعة <رقم> - ضبط السرعة (0.1 ~ 10)

أوامر نيك ام ~ وبعص امه
━━━━━━━━━━━━━━━━━━━━━━━━━
نيك ام (رد) - بدء هجوم مستمر مع رد على رسالة الشخص 

نيك ام <اسم> - بدء هجوم مستمر باسم 
مثال < نيك ام محمد > يحط بدايه السطر اسم محمد 


وقف نيك امه - يوقف نيك ام

━━━━━━━━━━━━━━━━━━━━━━━━━ 
أوامر بعص امه (يبعص امه كل ما ارسل رساله يرد عليها وين ماكان ب اي قروب و اي مكان):
━━━━━━━━━━━━━━━━━━━━━━━━━
بعص امه (رد) - يرد على كل رسالة من الشخص في أي قروب (سطور نيك ام)

وقف بعص امه - يوقف بعص فكسمه المخيس 

أمر اضربه (يرد ب سطور فرديات على رساله):
━━━━━━━━━━━━━━━━━━━━━━━━━
اضربه - يقعد يكتب سطور فرديات ب الشات (بدون رد) ويعدل لـ "ب اضرب امه"
اضربه (رد) - يعدل لـ "ب اضرب امه" ويبدأ هجوم مستمر مع رد على رسالة الشخص
وقف ضرب - إيقاف اضربه

أوامر التوقيف:
━━━━━━━━━━━━━━━━━━━━━━━━━
وقف الكل - يوقف جميع الهجمات دفعة واحدة (نيك ام، بعص امه، ضرب، تسطير)

وقف بعص امه - يوقف بعص كسمه المخمج 

وقف نيك ام - يوقف نيك امه المخيس

وقف جلد - يوقف تسطير 

وقف ضرب - يوقف الضرب 

أوامر إضافة السطور:
━━━━━━━━━━━━━━━━━━━━━━━━━
اضافه سطر ل نيك ام وبعص امه <النص>
اضافه سطر ل تسطير <النص>
اضافه سطر ل ضرب <النص>

أوامر حذف السطور:
━━━━━━━━━━━━━━━━━━━━━━━━━
حذف سطر <النص> - يحذف السطر من أي قائمة
عرض الرسائل المزروفه - عرض السطور المزروفة
احذف الرسائل المزروفه - حذف جميع السطور المزروفة
ازرفه (رد) - إضافة السطر لقائمة نيك ام وبعص امه

أوامر الكتم:
━━━━━━━━━━━━━━━━━━━━━━━━━
اخرس (رد) - يكتم الشخص ويحذف رسائله الجديدة في هذا الشات (رسالة الأمر تبقى)
اخرسس (رد) - تعدل لـ "اخرسسس ي ابن القحبه" + كتم
اخرسو - كتم جميع الأعضاء في هذا الشات

أوامر فك الكتم:
━━━━━━━━━━━━━━━━━━━━━━━━━
تنفس (رد) - فك كتم في هذا الشات 
تكلم يا ابن الزنوه (رد) - فك كتم في هذا الشات 

فك كتم الكل - فك كتم الكل في هذا الشات

أوامر إضافية:
━━━━━━━━━━━━━━━━━━━━━━━━━
حذف رسايلي - حذف آخر 1000 رسالة من المحادثة (خاص أو قروب) عشان تتجنب الباند 

حفظ الرسايل المؤقته - مثلا وحده عرضت لك صوره موقته تسوي رد على الرساله وتكتب تحويل يحفظ الصوره ويرسلها ب الرسايل المحفوظه 
بحث يوت - تكتب يوت مع اسم الاغنيه يرسل لك المقطع mp3 (يبحث في يوتيوب)
تحميل تيك - تحميل تيك <رابط المقطع الي تبي تحمله > يحمل لك المقطع او الصوره ويرسلها في لك
كشف الهمسه (رد) - كشف رسالة الهمسه
أذاعه (رد) - إذاعة الرسالة للجميع
تفليش القروب - طرد جميع الأعضاء
قائمة السطور - عرض الإحصائيات
قائمه الكتم - عرض قائمة المكتومين

معلومات:
━━━━━━━━━━━━━━━━━━━━━━━━━
نظام منع التكرار: مفعل (آخر 10 سطور)
جميع الإشعارات ترسل للرسائل المحفوظة
السرعة الحالية: {spam_speed} ثانية

تم التطوير بواسطة سورس ابو حمد & خطر
    """.format(spam_speed=spam_speed)
    
    await event.delete()
    await client.send_message(event.chat_id, help_text)

# ===================== القائمة المنسدلة (Inline Query) =====================
@client.on(InlineQuery())
async def inline_help(event):
    if event.text.strip() != "اوامر":
        return
    
    spam_text = """
أوامر التسطير
__________________

اصمل - يقعد يسطر (بدون رد)
اصمل مع ريبلاي - يقعد يسطره مع رد على نفس الرسالة

تغيير امر التسطير <الامر الجديد> يعني الحين تبي تسطر بدون لا أحد يكشفك بيدك تغيير أمر التسطير كل شوي وعشان تغيره تكتب > تغيير امر التسطير كس اختك <
الحين لو كتبت كس اختك ب يقعد يسطر بدال الأمر القديم الي هو اصمل

عدد الكلمات <رقم> - ضبط عدد الكلمات (1-20)
وقف جلد - إيقاف التسطير
السرعة <رقم> - ضبط السرعة (0.1 ~ 10)
"""

    insult_text = """
أوامر نيك ام ~ وبعص امه
__________________

نيك ام (رد) - بدء هجوم مستمر مع رد على رسالة الشخص
نيك ام <اسم> - بدء هجوم مستمر باسم (مثال: نيك ام محمد)

وقف نيك امه - يوقف نيك ام

بعص امه (رد) - يرد على كل رسالة من الشخص في أي قروب (سطور نيك ام)
وقف بعص امه - يوقف بعص فكسمه المخيس
"""

    hit_text = """
أوامر اضربه
__________________

اضربه - يقعد يكتب سطور فرديات ب الشات (بدون رد)
اضربه (رد) - يبدأ هجوم مستمر مع رد على رسالة الشخص
وقف ضرب - إيقاف اضربه
"""

    stop_text = """
أوامر التوقيف
__________________

وقف الكل - يوقف جميع الهجمات دفعة واحدة
وقف بعص امه - يوقف بعص كسمه المخمج
وقف نيك ام - يوقف نيك امه المخيس
وقف جلد - يوقف تسطير
وقف ضرب - يوقف الضرب
"""

    add_text = """
أوامر إضافة السطور
__________________

اضافه سطر ل نيك ام وبعص امه <النص>
اضافه سطر ل تسطير <النص>
اضافه سطر ل ضرب <النص>
"""

    del_text = """
أوامر حذف السطور
__________________

حذف سطر <النص> - يحذف السطر من أي قائمة
عرض الرسائل المزروفه - عرض السطور المزروفة
احذف الرسائل المزروفه - حذف جميع السطور المزروفة
ازرفه (رد) - إضافة السطر لقائمة نيك ام وبعص امه
"""

    mute_text = """
أوامر الكتم وفك الكتم
__________________

اخرس (رد) - يكتم الشخص ويحذف رسائله الجديدة
اخرسس (رد) - تعدل لـ "اخرسسس ي ابن القحبه" + كتم
اخرسو - كتم جميع الأعضاء في هذا الشات

تنفس (رد) - فك كتم في هذا الشات
تكلم يا ابن الزنوه (رد) - فك كتم في هذا الشات
فك كتم الكل - فك كتم الكل
"""

    info_text = """
معلومات السورس
__________________

نظام منع التكرار: مفعل (آخر 10 سطور)
جميع الإشعارات ترسل للرسائل المحفوظة
السرعة الحالية: 1.0 ثانية
تم التطوير بواسطة سورس ابو حمد & خطر
"""

    results = [
        InlineQueryResultArticle(
            id="1",
            title="أوامر التسطير",
            description="افتح لتعرف أوامر التسطير...",
            input_message_content=InputBotInlineMessageText(spam_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="2",
            title="أوامر نيك ام ~ وبعص امه",
            description="افتح لتعرف أوامر النيك والبعص...",
            input_message_content=InputBotInlineMessageText(insult_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="3",
            title="أوامر اضربه",
            description="افتح لتعرف أوامر الضرب...",
            input_message_content=InputBotInlineMessageText(hit_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="4",
            title="أوامر التوقيف",
            description="افتح لتعرف أوامر وقف الهجمات...",
            input_message_content=InputBotInlineMessageText(stop_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="5",
            title="أوامر إضافة السطور",
            description="افتح لإضافة سطور جديدة...",
            input_message_content=InputBotInlineMessageText(add_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="6",
            title="أوامر حذف السطور",
            description="افتح لحذف السطور...",
            input_message_content=InputBotInlineMessageText(del_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="7",
            title="أوامر الكتم",
            description="افتح لتعرف أوامر الكتم والفك...",
            input_message_content=InputBotInlineMessageText(mute_text, parse_mode=None)
        ),
        InlineQueryResultArticle(
            id="8",
            title="معلومات السورس",
            description="افتح لتعرف إحصائيات السورس...",
            input_message_content=InputBotInlineMessageText(info_text, parse_mode=None)
        ),
    ]

    await event.answer(results, cache_time=0, switch_pm_text="Welcome ~ قائمة أوامر سورس ابو حمد & خطر")

# ===================== تشغيل السورس =====================
async def main():
    global client
    
    print("جاري بدء تشغيل سورس ابو حمد & خطر...")
    
    try:
        await client.start()
        print("✅ تم الدخول إلى الحساب بنجاح!")
    except Exception as e:
        print(f"❌ خطأ في الدخول: {e}")
        return

    me = await client.get_me()
    print(f"✅ تم الدخول كـ: {me.first_name}")
    print(f"🆔 الايدي: {me.id}")
    
    print("=" * 50)
    print("🔥 سورس ابو حمد & خطر يعمل الان!")
    print(f"📊 عدد سطور نيك ام: {len(INSULT_STORAGE)}")
    print(f"📊 عدد سطور اضربه: {len(HIT_WORDS)}")
    print(f"📊 عدد كلمات التسطير: {len(SPAM_WORDS)}")
    print(f"📌 امر التسطير الحالي: {spam_command}")
    print(f"📌 عدد الكلمات الافتراضي: {spam_count}")
    print(f"⚡ السرعة الافتراضية: {spam_speed} ثانية")
    print("🔄 نظام منع التكرار: مفعل (اخر 10 سطور)")
    print("📨 جميع الاشعارات ترسل للرسائل المحفوظة")
    print("🛑 امر وقف الكل: يوقف جميع الهجمات دفعة واحدة")
    print("🎵 بحث يوت: يبحث في يوتيوب")
    print("=" * 50)
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف السورس")
    except Exception as e:
        print(f"❌ خطأ عام: {e}")