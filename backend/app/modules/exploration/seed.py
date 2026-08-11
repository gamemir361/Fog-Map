from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session
from app.core.database import Base, engine
from app.modules.exploration.models import POI, POIDetail, User


def seed_exploration_data():
    from app.modules.exploration.repository import clear_poi_cache
    clear_poi_cache()
    session = Session(bind=engine)
    try:
        if session.query(POI).count() < 30:
            session.query(POIDetail).delete()
            session.query(POI).delete()

            pois_data = [
                # --- فرهنگ و تاریخ (Culture & History) ---
                ("کاخ گلستان", "culture", "POINT(51.4200 35.6790)", "میراث جهانی یونسکو با تالارهای آینه‌کاری و عمارت شمس‌العماره.", {"nature": 0.3, "history": 0.98, "crowded": 0.5, "quiet": 0.4, "nightlife": 0.1, "luxury": 0.8, "budget": 0.4, "romantic": 0.7, "family": 0.7, "study": 0.6, "photography": 0.95, "food": 0.3}),
                ("میدان و برج آزادی", "culture", "POINT(51.3347 35.6997)", "نماد مدرن کلان‌شهر تهران با معماری تلفیقی ساسانی و اسلامی.", {"nature": 0.2, "history": 0.92, "crowded": 0.5, "quiet": 0.4, "nightlife": 0.5, "luxury": 0.4, "budget": 0.7, "romantic": 0.5, "family": 0.7, "study": 0.5, "photography": 0.95, "food": 0.3}),
                ("تئاتر شهر", "culture", "POINT(51.4055 35.7020)", "مهم‌ترین مرکز هنرهای نمایشی ایران با معماری استوانه‌ای منحصربه‌فرد.", {"nature": 0.2, "history": 0.85, "crowded": 0.7, "quiet": 0.3, "nightlife": 0.7, "luxury": 0.5, "budget": 0.6, "romantic": 0.7, "family": 0.5, "study": 0.7, "photography": 0.9, "food": 0.5}),
                ("کاخ سعدآباد", "culture", "POINT(51.4220 35.8150)", "مجموعه تاریخی ۱۱۰ هکتاری شامل ۱۸ کاخ و موزه در دامنه البرز.", {"nature": 0.9, "history": 0.96, "crowded": 0.4, "quiet": 0.7, "nightlife": 0.1, "luxury": 0.9, "budget": 0.3, "romantic": 0.85, "family": 0.8, "study": 0.5, "photography": 0.98, "food": 0.4}),
                ("کاخ نیاوران", "culture", "POINT(51.4720 35.8110)", "مجموعه کاخ‌ها و موزه با معماری مدرن ایرانی در باغی سرسبز.", {"nature": 0.85, "history": 0.92, "crowded": 0.4, "quiet": 0.7, "nightlife": 0.1, "luxury": 0.88, "budget": 0.3, "romantic": 0.8, "family": 0.8, "study": 0.5, "photography": 0.95, "food": 0.4}),
                ("موزه هنرهای معاصر", "culture", "POINT(51.3905 35.7110)", "گنجینه شاهکارهای هنر نوگرا با معماری بادگیرگونه کامران دیبا.", {"nature": 0.4, "history": 0.8, "crowded": 0.3, "quiet": 0.8, "nightlife": 0.1, "luxury": 0.7, "budget": 0.5, "romantic": 0.7, "family": 0.5, "study": 0.85, "photography": 0.92, "food": 0.2}),
                ("موزه ملی ایران", "culture", "POINT(51.4150 35.6880)", "مادر موزه‌های ایران شامل آثار باستانی از دوران پارینه‌سنگی تا اسلامی.", {"nature": 0.1, "history": 0.99, "crowded": 0.4, "quiet": 0.7, "nightlife": 0.1, "luxury": 0.6, "budget": 0.6, "romantic": 0.4, "family": 0.75, "study": 0.8, "photography": 0.88, "food": 0.2}),
                ("سردر باغ ملی", "culture", "POINT(51.4130 35.6860)", "بنای تاریخی کاشیکاری‌شده از اواخر دوران قاجار.", {"nature": 0.2, "history": 0.9, "crowded": 0.4, "quiet": 0.6, "nightlife": 0.3, "luxury": 0.4, "budget": 0.8, "romantic": 0.7, "family": 0.6, "study": 0.5, "photography": 0.95, "food": 0.3}),
                ("موزه آبگینه و سفالینه", "culture", "POINT(51.4145 35.6940)", "عمارت تاریخی قوام‌السلطنه با معماری چوبی و شیشه‌ای منحصربه‌فرد.", {"nature": 0.3, "history": 0.9, "crowded": 0.3, "quiet": 0.8, "nightlife": 0.1, "luxury": 0.75, "budget": 0.5, "romantic": 0.8, "family": 0.6, "study": 0.7, "photography": 0.93, "food": 0.2}),
                ("خانه مقدم", "culture", "POINT(51.4080 35.6870)", "باارزش‌ترین خانه قاجاری جهان با کاشیکاری‌های الوان و حیاط ایرانی.", {"nature": 0.5, "history": 0.95, "crowded": 0.3, "quiet": 0.85, "nightlife": 0.1, "luxury": 0.7, "budget": 0.6, "romantic": 0.9, "family": 0.6, "study": 0.65, "photography": 0.98, "food": 0.4}),
                ("باغ موزه قصر", "culture", "POINT(51.4450 35.7230)", "نخستین زندان متمرکز تهران تبدیل شده به بوستان و موزه تاریخ.", {"nature": 0.6, "history": 0.88, "crowded": 0.3, "quiet": 0.7, "nightlife": 0.2, "luxury": 0.4, "budget": 0.7, "romantic": 0.5, "family": 0.7, "study": 0.6, "photography": 0.85, "food": 0.3}),
                ("خانه هنرمندان ایران", "culture", "POINT(51.4180 35.7100)", "پاتوق هنرمندان و سینماگران در بوستان باغ هنرمندان.", {"nature": 0.6, "history": 0.7, "crowded": 0.6, "quiet": 0.65, "nightlife": 0.6, "luxury": 0.5, "budget": 0.6, "romantic": 0.8, "family": 0.65, "study": 0.8, "photography": 0.88, "food": 0.7}),
                ("باغ فردوس و موزه سینما", "culture", "POINT(51.4255 35.8080)", "عمارت قاجاری درمیان چنارهای کهنسال تجریش و موزه سینما.", {"nature": 0.6, "history": 0.88, "crowded": 0.4, "quiet": 0.7, "nightlife": 0.5, "luxury": 0.6, "budget": 0.5, "romantic": 0.92, "family": 0.7, "study": 0.6, "photography": 0.94, "food": 0.6}),
                ("موزه فرش ایران", "culture", "POINT(51.3910 35.7130)", "نمایشگاه شاهکارهای قالی‌بافی اصیل ایرانی در ضلع شمالی پارک لاله.", {"nature": 0.4, "history": 0.92, "crowded": 0.2, "quiet": 0.85, "nightlife": 0.1, "luxury": 0.7, "budget": 0.5, "romantic": 0.5, "family": 0.6, "study": 0.7, "photography": 0.85, "food": 0.2}),
                ("موزه دفاع مقدس", "culture", "POINT(51.4280 35.7520)", "مجموعه موزه مدرن با فناوری‌های چندرسانه‌ای و باغ‌دره اراضی عباس‌آباد.", {"nature": 0.6, "history": 0.85, "crowded": 0.3, "quiet": 0.7, "nightlife": 0.2, "luxury": 0.5, "budget": 0.7, "romantic": 0.3, "family": 0.85, "study": 0.7, "photography": 0.8, "food": 0.3}),
                ("موزه زمان", "culture", "POINT(51.4190 35.8030)", "عمارت گچ‌بری شده ناصرالدین‌شاهی با ساعت‌های آفتابی و تاریخی.", {"nature": 0.65, "history": 0.9, "crowded": 0.3, "quiet": 0.8, "nightlife": 0.2, "luxury": 0.75, "budget": 0.4, "romantic": 0.9, "family": 0.7, "study": 0.6, "photography": 0.96, "food": 0.6}),
                ("برج میلاد", "culture", "POINT(51.3753 35.7447)", "ششمین برج مخابراتی بلند جهان با مرکز همایش‌ها و رستوران گردان.", {"nature": 0.3, "history": 0.4, "crowded": 0.7, "quiet": 0.3, "nightlife": 0.85, "luxury": 0.95, "budget": 0.2, "romantic": 0.85, "family": 0.85, "study": 0.3, "photography": 0.96, "food": 0.8}),

                # --- طبیعت و بوستان‌ها (Nature & Parks) ---
                ("پل طبیعت", "nature", "POINT(51.4215 35.7548)", "سازه پیاده‌راه مدرن با دید بی‌نظیر از اتوبان مدرس و کوه‌های البرز.", {"nature": 0.9, "history": 0.2, "crowded": 0.6, "quiet": 0.5, "nightlife": 0.7, "luxury": 0.6, "budget": 0.5, "romantic": 0.9, "family": 0.85, "study": 0.4, "photography": 0.98, "food": 0.7}),
                ("پارک جمشیدیه", "nature", "POINT(51.4645 35.8235)", "بوستان صخره‌ای کوهستانی در نیاوران با درختان کهنسال و آبشار.", {"nature": 0.98, "history": 0.3, "crowded": 0.3, "quiet": 0.9, "nightlife": 0.3, "luxury": 0.3, "budget": 0.7, "romantic": 0.8, "family": 0.8, "study": 0.6, "photography": 0.9, "food": 0.5}),
                ("پارک ملت", "nature", "POINT(51.4050 35.7770)", "بوستان سرسبز ولیعصر با دریاچه مصنوعی و قطار تفریحی.", {"nature": 0.92, "history": 0.4, "crowded": 0.5, "quiet": 0.7, "nightlife": 0.6, "luxury": 0.4, "budget": 0.7, "romantic": 0.75, "family": 0.9, "study": 0.5, "photography": 0.85, "food": 0.5}),
                ("پارک لاله", "nature", "POINT(51.3912 35.7115)", "بوستان مرکزی تهران با پوشش گیاهی غنی و فضای پیاده‌روی.", {"nature": 0.88, "history": 0.5, "crowded": 0.5, "quiet": 0.7, "nightlife": 0.4, "luxury": 0.3, "budget": 0.8, "romantic": 0.6, "family": 0.85, "study": 0.75, "photography": 0.8, "food": 0.4}),
                ("دربند", "nature", "POINT(51.4285 35.8200)", "مسیر کوهنوردی با آب و هوای خنک، رودخانه و سفره‌خانه‌های کوهپایه‌ای.", {"nature": 0.88, "history": 0.3, "crowded": 0.85, "quiet": 0.3, "nightlife": 0.9, "luxury": 0.5, "budget": 0.5, "romantic": 0.75, "family": 0.75, "study": 0.1, "photography": 0.8, "food": 0.98}),
                ("درکه", "nature", "POINT(51.3950 35.8080)", "مسیر پیاده‌روی کوهستانی با رستوران‌های سنتی و رودخانه درکه.", {"nature": 0.92, "history": 0.3, "crowded": 0.7, "quiet": 0.5, "nightlife": 0.6, "luxury": 0.4, "budget": 0.6, "romantic": 0.7, "family": 0.8, "study": 0.2, "photography": 0.82, "food": 0.9}),
                ("بوستان آب و آتش", "nature", "POINT(51.4190 35.7560)", "پارک مدرن با فواره‌های آب، برج‌های آتش و کالسکه رانی.", {"nature": 0.85, "history": 0.1, "crowded": 0.7, "quiet": 0.4, "nightlife": 0.75, "luxury": 0.5, "budget": 0.6, "romantic": 0.8, "family": 0.9, "study": 0.3, "photography": 0.88, "food": 0.75}),
                ("بوستان طالقانی", "nature", "POINT(51.4240 35.7530)", "پارک جنگلی فوق‌العاده زیبا متصل به پل طبیعت با پرچم بزرگ ایران.", {"nature": 0.95, "history": 0.2, "crowded": 0.4, "quiet": 0.8, "nightlife": 0.3, "luxury": 0.2, "budget": 0.8, "romantic": 0.7, "family": 0.85, "study": 0.6, "photography": 0.85, "food": 0.3}),
                ("پارک پردیسان", "nature", "POINT(51.3620 35.7420)", "پارک گسترده برای کایت‌سواری، دوچرخه‌سواری و دیدن موزه تنوع زیستی.", {"nature": 0.9, "history": 0.1, "crowded": 0.4, "quiet": 0.8, "nightlife": 0.4, "luxury": 0.2, "budget": 0.8, "romantic": 0.6, "family": 0.85, "study": 0.5, "photography": 0.8, "food": 0.2}),
                ("دریاچه چیتگر (شهدای خلیج فارس)", "nature", "POINT(51.2150 35.7480)", "بزرگترین دریاچه مصنوعی تهران با بام لند و قایقرانی.", {"nature": 0.85, "history": 0.1, "crowded": 0.8, "quiet": 0.4, "nightlife": 0.8, "luxury": 0.7, "budget": 0.5, "romantic": 0.85, "family": 0.95, "study": 0.2, "photography": 0.9, "food": 0.85}),
                ("پارک جنگلی چیتگر", "nature", "POINT(51.2000 35.7350)", "پارک جنگلی وسیع غرب تهران با پیست دوچرخه‌سواری حرفه‌ای.", {"nature": 0.98, "history": 0.1, "crowded": 0.3, "quiet": 0.85, "nightlife": 0.2, "luxury": 0.1, "budget": 0.9, "romantic": 0.6, "family": 0.85, "study": 0.4, "photography": 0.75, "food": 0.3}),
                ("بوستان ساعی", "nature", "POINT(51.4110 35.7320)", "پارک پلکانی با گونه‌های جانوری و درختان سر به فلک کشیده خیابان ولیعصر.", {"nature": 0.9, "history": 0.4, "crowded": 0.5, "quiet": 0.7, "nightlife": 0.4, "luxury": 0.3, "budget": 0.7, "romantic": 0.75, "family": 0.8, "study": 0.6, "photography": 0.82, "food": 0.3}),
                ("پارک نیاوران", "nature", "POINT(51.4700 35.8130)", "پارک با صفا با طبقات هندسی متقارن و قنات‌های زلال شمال تهران.", {"nature": 0.92, "history": 0.5, "crowded": 0.4, "quiet": 0.75, "nightlife": 0.4, "luxury": 0.5, "budget": 0.6, "romantic": 0.7, "family": 0.85, "study": 0.6, "photography": 0.85, "food": 0.3}),
                ("ژوراسیک پارک تهران", "nature", "POINT(51.3720 35.7820)", "پارک موضوعی دایناسورهای متحرک غول‌پیکر در سعادت‌آباد.", {"nature": 0.6, "history": 0.3, "crowded": 0.6, "quiet": 0.3, "nightlife": 0.2, "luxury": 0.5, "budget": 0.5, "romantic": 0.3, "family": 0.98, "study": 0.3, "photography": 0.8, "food": 0.5}),
                ("باغ ملی گیاه‌شناسی", "nature", "POINT(51.1850 35.7400)", "یکی از ۱۰ باغ گیاه‌شناسی برتر جهان با کلکسیون گیاهان همالیا و چین.", {"nature": 0.99, "history": 0.3, "crowded": 0.2, "quiet": 0.95, "nightlife": 0.1, "luxury": 0.6, "budget": 0.6, "romantic": 0.9, "family": 0.8, "study": 0.7, "photography": 0.98, "food": 0.3}),
                ("بوستان گفتگو", "nature", "POINT(51.3780 35.7270)", "پارک مدرن با سبک‌های باغ‌سازی ایرانی، انگلیسی و ایتالیایی.", {"nature": 0.9, "history": 0.3, "crowded": 0.4, "quiet": 0.8, "nightlife": 0.3, "luxury": 0.4, "budget": 0.7, "romantic": 0.75, "family": 0.85, "study": 0.6, "photography": 0.88, "food": 0.4}),

                # --- انرژی، غذا و بازارهای شلوغ (Energy & Food & Markets) ---
                ("بازار تجریش", "energy", "POINT(51.4320 35.8050)", "بازار سنتی سرپوشیده با تکیه تاریخی، حجره‌های میوه نایاب و غذا.", {"nature": 0.2, "history": 0.8, "crowded": 0.95, "quiet": 0.1, "nightlife": 0.7, "luxury": 0.4, "budget": 0.7, "romantic": 0.4, "family": 0.8, "study": 0.1, "photography": 0.88, "food": 0.92}),
                ("بازار بزرگ تهران", "energy", "POINT(51.4190 35.6740)", "قلب اقتصادی و تاریخی ایران با سراها و تیمچه‌های متعدد.", {"nature": 0.1, "history": 0.95, "crowded": 0.99, "quiet": 0.05, "nightlife": 0.1, "luxury": 0.3, "budget": 0.9, "romantic": 0.3, "family": 0.7, "study": 0.1, "photography": 0.85, "food": 0.85}),
                ("خیابان سی تیر", "energy", "POINT(51.4140 35.6920)", "استریت‌فود سنگفرش تهران با دکه‌های کباب، فلافل و کافه‌های سیار.", {"nature": 0.1, "history": 0.85, "crowded": 0.9, "quiet": 0.2, "nightlife": 0.95, "luxury": 0.3, "budget": 0.7, "romantic": 0.65, "family": 0.7, "study": 0.2, "photography": 0.82, "food": 0.98}),
                ("بام تهران (ولنجک)", "energy", "POINT(51.4060 35.8250)", "ارتفاعات توچال با سورتمه، زیپ‌لاین، کافه‌ها و منظره ۳۶۰ درجه شب.", {"nature": 0.75, "history": 0.1, "crowded": 0.8, "quiet": 0.4, "nightlife": 0.9, "luxury": 0.6, "budget": 0.6, "romantic": 0.85, "family": 0.8, "study": 0.2, "photography": 0.95, "food": 0.8}),
                ("مرکز خرید ایران مال", "energy", "POINT(51.1920 35.7530)", "یکی از ۵ مگامال بزرگ جهان با باغ ایرانی، شربت‌خانه و پیست یخ.", {"nature": 0.4, "history": 0.3, "crowded": 0.8, "quiet": 0.3, "nightlife": 0.7, "luxury": 0.98, "budget": 0.2, "romantic": 0.7, "family": 0.9, "study": 0.5, "photography": 0.92, "food": 0.9}),
                ("بام لند چیتگر", "energy", "POINT(51.2180 35.7460)", "مجموعه رستوران‌های برند و فضای پیاده‌روی ساحلی دریاچه چیتگر.", {"nature": 0.7, "history": 0.1, "crowded": 0.8, "quiet": 0.4, "nightlife": 0.85, "luxury": 0.85, "budget": 0.3, "romantic": 0.9, "family": 0.85, "study": 0.3, "photography": 0.9, "food": 0.95}),
                ("مجتمع کوروش مال", "energy", "POINT(51.3150 35.7380)", "مرکز خرید و پردیس سینمایی شلوغ در اتوبان ستاری.", {"nature": 0.1, "history": 0.1, "crowded": 0.9, "quiet": 0.2, "nightlife": 0.8, "luxury": 0.7, "budget": 0.5, "romantic": 0.6, "family": 0.9, "study": 0.2, "photography": 0.7, "food": 0.88}),
                ("بازارچه ستارخان", "energy", "POINT(51.3650 35.7180)", "راسته پوشاک و فست‌فودهای معروف غرب تهران.", {"nature": 0.1, "history": 0.2, "crowded": 0.85, "quiet": 0.2, "nightlife": 0.8, "luxury": 0.3, "budget": 0.8, "romantic": 0.4, "family": 0.8, "study": 0.1, "photography": 0.6, "food": 0.9}),
                ("فودکورت چارسو", "energy", "POINT(51.4110 35.6930)", "پردیس سینمایی و طبقه بزرگ رستوران‌های تقاطع جمهوری و حافظ.", {"nature": 0.1, "history": 0.2, "crowded": 0.85, "quiet": 0.3, "nightlife": 0.7, "luxury": 0.6, "budget": 0.6, "romantic": 0.6, "family": 0.8, "study": 0.4, "photography": 0.75, "food": 0.92}),
                ("کوچه مروی", "energy", "POINT(51.4230 35.6770)", "راسته شکلات، قهوه، عود و ناصرخسرو با بناهای قدیمی.", {"nature": 0.1, "history": 0.85, "crowded": 0.9, "quiet": 0.2, "nightlife": 0.2, "luxury": 0.3, "budget": 0.8, "romantic": 0.4, "family": 0.6, "study": 0.1, "photography": 0.8, "food": 0.8}),
                ("بازارچه باب همایون", "energy", "POINT(51.4180 35.6810)", "راسته سوغات و پوشاک نوستالژیک در میدان امام خمینی.", {"nature": 0.1, "history": 0.85, "crowded": 0.85, "quiet": 0.2, "nightlife": 0.6, "luxury": 0.2, "budget": 0.85, "romantic": 0.4, "family": 0.7, "study": 0.1, "photography": 0.75, "food": 0.85}),
                ("فلکه اول صادقیه", "energy", "POINT(51.3380 35.7200)", "میدان پرتردد با آبمیوه‌فروشی‌ها و ساندویچی‌های خاطره‌انگیز.", {"nature": 0.1, "history": 0.2, "crowded": 0.9, "quiet": 0.1, "nightlife": 0.85, "luxury": 0.2, "budget": 0.85, "romantic": 0.3, "family": 0.7, "study": 0.1, "photography": 0.5, "food": 0.95}),

                # --- دنج، مطالعه و آرامش (Quiet & Study) ---
                ("کافه کتاب قلمستان", "quiet", "POINT(51.4020 35.7080)", "فضایی دنج با بوی قهوه تازه، کتاب‌های متنوع و صندلی‌های مطالعه.", {"nature": 0.2, "history": 0.4, "crowded": 0.2, "quiet": 0.95, "nightlife": 0.4, "luxury": 0.3, "budget": 0.6, "romantic": 0.6, "family": 0.4, "study": 0.98, "photography": 0.6, "food": 0.7}),
                ("باغ کتاب تهران", "quiet", "POINT(51.4270 35.7510)", "بزرگترین فروشگاه کتاب و سرگرمی علمی کشور در اراضی عباس‌آباد.", {"nature": 0.6, "history": 0.2, "crowded": 0.6, "quiet": 0.8, "nightlife": 0.3, "luxury": 0.5, "budget": 0.7, "romantic": 0.6, "family": 0.95, "study": 0.95, "photography": 0.85, "food": 0.6}),
                ("کتابخانه ملی ایران", "quiet", "POINT(51.4250 35.7530)", "مخزن جامع اسناد و تالارهای تخصصی مطالعه پژوهشگران.", {"nature": 0.5, "history": 0.5, "crowded": 0.3, "quiet": 0.99, "nightlife": 0.1, "luxury": 0.4, "budget": 0.8, "romantic": 0.3, "family": 0.3, "study": 1.0, "photography": 0.7, "food": 0.3}),
                ("کافه نزدیک کتاب", "quiet", "POINT(51.4150 35.7010)", "کافه طبقه دوم زیر پله‌های خیابان کریم‌خان با تراس سرسبز دنج.", {"nature": 0.4, "history": 0.4, "crowded": 0.3, "quiet": 0.9, "nightlife": 0.5, "luxury": 0.4, "budget": 0.6, "romantic": 0.8, "family": 0.4, "study": 0.92, "photography": 0.7, "food": 0.75}),
                ("کافه رویداد", "quiet", "POINT(51.4010 35.7140)", "محیط اشتراکی و کار اشتراکی کارآفرینان و برنامه‌نویسان در بلوار کشاورز.", {"nature": 0.3, "history": 0.2, "crowded": 0.3, "quiet": 0.88, "nightlife": 0.3, "luxury": 0.4, "budget": 0.6, "romantic": 0.5, "family": 0.3, "study": 0.95, "photography": 0.6, "food": 0.7}),
                ("کافه گودو یاس", "quiet", "POINT(51.4160 35.6980)", "عمارت تاریخی بازسازی‌شده با حیاط مرکزی، حوض ماهی و فیلکس وگنر.", {"nature": 0.5, "history": 0.85, "crowded": 0.4, "quiet": 0.85, "nightlife": 0.5, "luxury": 0.6, "budget": 0.5, "romantic": 0.92, "family": 0.5, "study": 0.8, "photography": 0.95, "food": 0.8}),
                ("کافه نادري", "quiet", "POINT(51.4130 35.6950)", "نوستالژیک‌ترین کافه تهران، پاتوق صادق هدایت و جلال آل احمد.", {"nature": 0.1, "history": 0.98, "crowded": 0.5, "quiet": 0.75, "nightlife": 0.2, "luxury": 0.4, "budget": 0.7, "romantic": 0.7, "family": 0.6, "study": 0.75, "photography": 0.88, "food": 0.7}),

                # --- شب‌گردی و عکاسی (Nightlife & Photography) ---
                ("خیابان ولیعصر (بخش چنارها)", "photography", "POINT(51.4100 35.7400)", "بلندترین خیابان خاورمیانه با جوی‌های جاری و تونل درختان چنار.", {"nature": 0.7, "history": 0.8, "crowded": 0.6, "quiet": 0.5, "nightlife": 0.8, "luxury": 0.5, "budget": 0.7, "romantic": 0.9, "family": 0.75, "study": 0.5, "photography": 0.98, "food": 0.6}),
                ("میدان صنعت و شهرک غرب", "nightlife", "POINT(51.3680 35.7530)", "بلوار پاکنژاد و مجتمع‌های شیک با شب‌های روشن و کافه‌های مدرن.", {"nature": 0.3, "history": 0.1, "crowded": 0.7, "quiet": 0.4, "nightlife": 0.9, "luxury": 0.8, "budget": 0.4, "romantic": 0.7, "family": 0.7, "study": 0.4, "photography": 0.8, "food": 0.85}),
                ("بلوار اندرزگو", "nightlife", "POINT(51.4480 35.7980)", "راسته ماشین‌بازی، بستنی‌فروشی‌های معروف و شب‌گردی شمال شهر.", {"nature": 0.2, "history": 0.1, "crowded": 0.9, "quiet": 0.1, "nightlife": 0.98, "luxury": 0.9, "budget": 0.3, "romantic": 0.6, "family": 0.6, "study": 0.1, "photography": 0.7, "food": 0.92}),
                ("کوهسار و بام شهران", "nightlife", "POINT(51.2750 35.7720)", "ارتفاعات غرب تهران با دید پانورامیک به چراغ‌های شبانه شهر.", {"nature": 0.8, "history": 0.1, "crowded": 0.5, "quiet": 0.7, "nightlife": 0.88, "luxury": 0.3, "budget": 0.8, "romantic": 0.8, "family": 0.7, "study": 0.3, "photography": 0.9, "food": 0.4}),
            ]

            LEGENDARY_POIS = {"کاخ گلستان", "باغ ملی گیاه‌شناسی", "کتابخانه ملی ایران"}
            EPIC_POIS = {"میدان و برج آزادی", "برج میلاد", "پل طبیعت", "کاخ سعدآباد", "کاخ نیاوران", "دریاچه چیتگر (شهدای خلیج فارس)", "مرکز خرید ایران مال"}
            RARE_POIS = {"خانه مقدم", "بازار بزرگ تهران", "بازار تجریش", "باغ فردوس و موزه سینما", "موزه هنرهای معاصر", "موزه ملی ایران", "بام تهران (ولنجک)", "تئاتر شهر"}

            for name, category, geom_wkt, desc, vibe_dict in pois_data:
                if name in LEGENDARY_POIS:
                    rarity_val = "legendary"
                elif name in EPIC_POIS:
                    rarity_val = "epic"
                elif name in RARE_POIS:
                    rarity_val = "rare"
                else:
                    rarity_val = "common"

                poi = POI(
                    name=name,
                    category=category,
                    geometry=WKTElement(geom_wkt, srid=4326),
                    rarity=rarity_val,
                )
                session.add(poi)
                session.flush()

                detail = POIDetail(
                    location_id=poi.id,
                    description=desc,
                    **vibe_dict
                )
                session.add(detail)

        if session.query(User).count() == 0:
            user = User(username="explorer_1", score=120)
            session.add(user)
            session.flush()
            user.pref_nature = 0.8
            user.pref_history = 0.6
            user.pref_crowded = 0.3
            user.pref_quiet = 0.7
            user.pref_nightlife = 0.5
            user.pref_luxury = 0.4
            user.pref_budget = 0.6
            user.pref_romantic = 0.7
            user.pref_family = 0.7
            user.pref_study = 0.6
            user.pref_photography = 0.85
            user.pref_food = 0.5

        session.commit()
    finally:
        session.close()


def seed_exploration_events(session: Session = None):
    import datetime
    from app.modules.exploration.models import ExplorationEvent

    close_session = False
    if session is None:
        session = Session(bind=engine)
        close_session = True

    try:
        now = datetime.datetime.utcnow()

        events_data = [
            # --- Active Events ---
            {
                "title": "جشنواره فرهنگ و هنر کاخ گلستان",
                "description": "بازدید از تالارهای تاریخی آینه‌کاری و نمایشگاه صنایع‌دستی قاجار در عمارت گلستان.",
                "event_type": "cultural",
                "lat": 35.6790,
                "lon": 51.4200,
                "radius": 300.0,
                "xp_reward": 150,
                "starts_at": now - datetime.timedelta(days=2),
                "ends_at": now + datetime.timedelta(days=5),
            },
            {
                "title": "شب تاریخ و معماری بازار بزرگ",
                "description": "پیمایش شبانه سراها و تیمچه‌های تاریخی بازار کلان‌شهر تهران.",
                "event_type": "historical",
                "lat": 35.6740,
                "lon": 51.4190,
                "radius": 400.0,
                "xp_reward": 200,
                "starts_at": now - datetime.timedelta(days=1),
                "ends_at": now + datetime.timedelta(days=3),
            },
            {
                "title": "چالش معماری و نمادهای برج آزادی",
                "description": "کشف زوایای پنهان معماری نمادین برج آزادی و محوطه میدان.",
                "event_type": "challenge",
                "lat": 35.6997,
                "lon": 51.3347,
                "radius": 500.0,
                "xp_reward": 120,
                "starts_at": now - datetime.timedelta(hours=12),
                "ends_at": now + datetime.timedelta(days=2),
            },
            {
                "title": "پیمایش پاییزی باغ گیاه‌شناسی ملی",
                "description": "کاوش کلکسیون‌های نادر گیاهی از چین، هیمالیا و زاگرس در باغ ملی.",
                "event_type": "nature",
                "lat": 35.7400,
                "lon": 51.1850,
                "radius": 600.0,
                "xp_reward": 180,
                "starts_at": now - datetime.timedelta(days=3),
                "ends_at": now + datetime.timedelta(days=4),
            },
            # --- Ending Soon Event ---
            {
                "title": "کاوش فشرده گنجینه‌های خانه مقدم",
                "description": "فرصت پایانی برای کشف باارزش‌ترین کاشیکاری‌های الوان در خانه مقدم.",
                "event_type": "historical",
                "lat": 35.6870,
                "lon": 51.4080,
                "radius": 250.0,
                "xp_reward": 250,
                "starts_at": now - datetime.timedelta(hours=22),
                "ends_at": now + datetime.timedelta(hours=2),
            },
            # --- Scheduled / Upcoming Events ---
            {
                "title": "شب‌های روشن برج میلاد",
                "description": "رویداد پیش‌رو برای عکاسی پانورامیک شبانه از بام پایتخت.",
                "event_type": "exploration",
                "lat": 35.7447,
                "lon": 51.3753,
                "radius": 500.0,
                "xp_reward": 150,
                "starts_at": now + datetime.timedelta(days=2),
                "ends_at": now + datetime.timedelta(days=5),
            },
            {
                "title": "ماراتون عکاسی خیابان سی تیر",
                "description": "مسابقه عکاسی سنگفرش تاریخی و استریت‌فودهای خیابان ۳۰ تیر.",
                "event_type": "cultural",
                "lat": 35.6920,
                "lon": 51.4140,
                "radius": 350.0,
                "xp_reward": 160,
                "starts_at": now + datetime.timedelta(days=3),
                "ends_at": now + datetime.timedelta(days=7),
            },
            {
                "title": "چالش پیاده‌روی پل طبیعت و باغ کتاب",
                "description": "رویداد ورزشی-کاوشی عبور از پل طبیعت تا تالارهای مطالعه باغ کتاب.",
                "event_type": "challenge",
                "lat": 35.7548,
                "lon": 51.4215,
                "radius": 700.0,
                "xp_reward": 300,
                "starts_at": now + datetime.timedelta(days=5),
                "ends_at": now + datetime.timedelta(days=10),
            },
            # --- Ended Events ---
            {
                "title": "رویداد افتتاحیه سینمایی باغ فردوس",
                "description": "جشنواره خاتمه‌یافته موزه سینما در عمارت قاجاری باغ فردوس.",
                "event_type": "historical",
                "lat": 35.8080,
                "lon": 51.4255,
                "radius": 300.0,
                "xp_reward": 100,
                "starts_at": now - datetime.timedelta(days=10),
                "ends_at": now - datetime.timedelta(days=3),
            },
            {
                "title": "گردهمایی کاوشگران جمشیدیه",
                "description": "رویداد پایان‌یافته بوستان صخره‌ای جمشیدیه.",
                "event_type": "nature",
                "lat": 35.8235,
                "lon": 51.4645,
                "radius": 400.0,
                "xp_reward": 120,
                "starts_at": now - datetime.timedelta(days=14),
                "ends_at": now - datetime.timedelta(days=7),
            },
        ]

        for item in events_data:
            existing = session.query(ExplorationEvent).filter(ExplorationEvent.title == item["title"]).first()

            if now < item["starts_at"]:
                calc_status = "scheduled"
            elif now >= item["ends_at"]:
                calc_status = "ended"
            else:
                calc_status = "active"

            geom_wkt = f"POINT({item['lon']} {item['lat']})"

            if existing:
                existing.description = item["description"]
                existing.event_type = item["event_type"]
                existing.status = calc_status
                existing.latitude = item["lat"]
                existing.longitude = item["lon"]
                existing.radius_meters = item["radius"]
                existing.geometry = WKTElement(geom_wkt, srid=4326)
                existing.xp_reward = item["xp_reward"]
                existing.starts_at = item["starts_at"]
                existing.ends_at = item["ends_at"]
                existing.is_active = True
                existing.updated_at = datetime.datetime.utcnow()
            else:
                event_obj = ExplorationEvent(
                    title=item["title"],
                    description=item["description"],
                    event_type=item["event_type"],
                    status=calc_status,
                    latitude=item["lat"],
                    longitude=item["lon"],
                    radius_meters=item["radius"],
                    geometry=WKTElement(geom_wkt, srid=4326),
                    xp_reward=item["xp_reward"],
                    starts_at=item["starts_at"],
                    ends_at=item["ends_at"],
                    is_active=True,
                )
                session.add(event_obj)

        session.commit()
    finally:
        if close_session:
            session.close()
