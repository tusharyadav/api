from BeautifulSoup import BeautifulSoup, Tag
from base.models import NoImage
from base.serializers import BaseSerializer, BasePaginationSerializer, \
    ListBaseSerializer, get_no_image
from django.conf import settings
from images.models import Image
from images.serializers import ImageSerializer
from news.models import News, NewsRelatedContent,PartnerNewsInfo,RelatedNews
from rest_framework import serializers
import json
import re
from django.utils.translation import ugettext as _

IMAGE_TYPE_GALLERY = settings.IMAGE_TYPE_GALLERY



def get_image_version(image, version_type="image_version2"):

    IMAGE_VERSION = {'image_version2': {'large': 'martini_image_400_200', 
                                        'medium': 'martini_image_300_150',
                                        'small': 'martini_image_300_150', 
                                        'fullscreen': 'martini_image_400_200',
                                        'thumbnail_large': 'martini_image_300_150',
                                        }
                                    }
    
    version_type = version_type if version_type else "image_version2" 
    images_urls = {}
    for version, sizes in IMAGE_VERSION.items():
        images_urls[version_type] = {}
        for size, val in sizes.items():
            try:
                images_urls[version_type][size] = image.version_generate(val).url
            except Exception as exc:
                images_urls[version_type][size] = NoImage(path=get_no_image("martini")).image.version_generate(val).url

    return images_urls


class BaseNewsSerializer(BaseSerializer):
    related_news = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField('news_tags')
    tags_list = serializers.SerializerMethodField('news_tags_list')
    user = serializers.ReadOnlyField(source='user.name')
    profile_url = serializers.ReadOnlyField(source='user.get_absolute_url')
    amp_url = serializers.ReadOnlyField(source='get_amp_url')
    ucb_url = serializers.ReadOnlyField(source='get_ucb_url')
    friends_data = serializers.SerializerMethodField('get_friends_reading')
    mobile_text = serializers.SerializerMethodField('get_mobile_content')
    amp_content = serializers.ReadOnlyField()
    instant_content = serializers.ReadOnlyField()
    
    short_text = serializers.SerializerMethodField('get_short_content')
    #region_text = serializers.SerializerMethodField()
    """Below utm field is used to verify whether utm parameters need to send in link or not """
    #is_utm = serializers.ReadOnlyField()
    slideshow_images = serializers.SerializerMethodField()
    next_news = serializers.SerializerMethodField()
    object_region = serializers.SerializerMethodField()
    horizontal_image = serializers.SerializerMethodField()
    square_image = serializers.SerializerMethodField()
    
    news_thumbnail = serializers.SerializerMethodField('get_image')
    #original_image = serializers.SerializerMethodField()
    writers = serializers.ReadOnlyField(source='get_writers')
    is_sponsored = serializers.ReadOnlyField()
    sponsored = serializers.SerializerMethodField()
    related_content = serializers.SerializerMethodField()

    top_banner = serializers.ReadOnlyField(source="get_top_banner")
    lower_banner = serializers.ReadOnlyField(source="get_lower_banner")
    mobile_top_banner = serializers.ReadOnlyField(source="get_mobile_top_banner")
    mobile_lower_banner = serializers.ReadOnlyField(source="get_mobile_lower_banner")
    ads_url = serializers.ReadOnlyField()
    gallery_id =  serializers.ReadOnlyField()

    class Meta:
        model = News

    def get_sponsored(self, obj):
        if not hasattr(obj,"is_sponsored"):
            return {"logo": None,"content":None,"link":None}

        logo = obj.sponsored_logo.url if obj.sponsored_logo else None
        return {"logo": logo,"content":obj.sponsored_content,"link":obj.sponsored_link}
        

    
    def get_slideshow_images(self, obj):
        images = None
        if hasattr(obj,"gallery_id") and obj.gallery_id is not None:
            if hasattr(self,"host_det") and self.host_det == "app":
                images=Image.active.filter(gallery = obj.gallery,parent_id__isnull=True).order_by('sequence')
        else:
            images = Image.active.get_images_for_news(obj.id)
        if images:
            final_images = ImageSerializer(instance=images, user=self.user, token=self.auth_token, many=True, image_type=self.image_type)
            final_images.include_fields(('id', 'title', 'description', 'image', 'thumb', 'source', 'source_url'))
            return final_images.data
        else:
            return None
        
    def get_related_news(self, obj):
        return []
        # related_news = News.active.get_recent_news(obj)[:10]
        # serializer = NewsSerializer(instance=related_news, many=True, image_type=self.image_type)
        # serializer.include_fields(('id', 'title', 'short_text', 'url', 'first_video', 'first_image', 'created_date', 'data_content_type', 'category',"news_thumbnail",))
        # return serializer.data

    def news_tags(self, obj):
        return ((),())

    def news_tags_list(self, obj):
        return obj.get_tags()

    def get_object_region(self,obj):
        return _(settings.REGION_CATEGORY_TYPES[str(obj.region)])

    def get_friends_reading(self, obj):
        return []

    def get_mobile_content(self, obj):
        if obj.mobile_content:
            content = obj.mobile_content
        else:
            content = obj.content

        if not self.host_det:  # apps only
            content = content.replace("\n<br />\n", "\n")
        elif self.host_det == "android":
            content = content.replace("\n<br />\n", "\n")
            soup = BeautifulSoup(content)
            # if soup.findAll('iframe'):
            #     gh = soup.findAll('iframe')[0]['src']
            #     hh = soup.findAll('iframe')
            for p in soup.findAll("iframe"):
                if "youtube" in p['src']:
                    newTag = Tag(soup, "a")
                    newTag.attrs.append(("src", p.get('src')))
                    p.append(newTag)
            content = unicode(soup)
        if obj.source is not None and obj.source != '':
            content = content + "<p>Sources: " + obj.source.replace("<p>", "").replace("</p>", "") + "</p>"
        else:
            content = content

        content = obj.get_modified_content(content,content_type='mobile')
        return content

    def get_short_content(self, obj):
        from BeautifulSoup import BeautifulSoup
        # soup = BeautifulSoup(obj.content)
        soup = BeautifulSoup(obj.content, convertEntities=BeautifulSoup.HTML_ENTITIES)
        [s.extract() for s in soup('script')]
        data = ''.join(soup.findAll(text=True))[:200]
        data = soup.getText()
        data = re.sub(r'(\n)+|(\s)+', ' ', data)
        data = data.strip()
        return data
        
    def get_next_news(self, obj):
        return []

    def get_image(self, obj):
        original_image = None
        if obj.first_image:
            original_image=obj.first_image.url    
        if obj.first_video:
            original_image = obj.first_video

        if obj.category in (settings.QUIZ_TYPE, settings.LIST_TYPE):
            image = get_image_version(obj.get_image(), self.image_type)            
        else:
            image = self.get_image_version(obj.get_image(), IMAGE_TYPE_GALLERY)
        if "image_version1" in image:
            image["image_version1"]["original"] = original_image
        if "image_version2" in image:
            image["image_version2"]["original"] = original_image

        return image

    def get_horizontal_image(self, obj):
        if not obj.martini_horizontal:
            return self.get_image(obj)["image_version2"]

        original_image = None
        if obj.first_image:
            original_image=obj.first_image.url    
        if obj.first_video:
            original_image = obj.first_video

        image = get_image_version(obj.martini_horizontal, self.image_type)
        image["image_version2"]["original"] = original_image
        return image["image_version2"]

    def get_square_image(self, obj):
        if not obj.thumbnail:
            return self.get_image(obj)["image_version2"]

        original_image = None
        if obj.first_image:
            original_image=obj.first_image.url    
        if obj.first_video:
            original_image = obj.first_video

        image = self.get_image_version(obj.thumbnail, IMAGE_TYPE_GALLERY)  
        image["image_version2"]["original"] = original_image
        return image["image_version2"]
    
    def get_related_content(self, obj):
        return obj.get_related_content()
    
class ListNewsSerializer(ListBaseSerializer):
    def __init__(self, *args, **kwargs):
        super(ListNewsSerializer, self).__init__(*args, **kwargs)

class NewsLhSerializer(BaseNewsSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = PartnerNewsInfo
        list_serializer_class = ListNewsSerializer


    def get_image(self,obj):

        return obj.image_path.url



class NewsSerializer(BaseNewsSerializer):

    class Meta:
        model = News
        list_serializer_class = ListNewsSerializer

    first_image = serializers.SerializerMethodField()
    #slideshow_images = serializers.SerializerMethodField('get_slideshow_images')
    martini_image = serializers.SerializerMethodField()

    def get_first_image(self, obj):
        if hasattr(obj, 'thumbnail') and obj.thumbnail:
            image = self.get_image_version(obj.thumbnail, IMAGE_TYPE_GALLERY)
            return image
        elif obj.first_image:
            image = self.get_image_version(obj.first_image, IMAGE_TYPE_GALLERY)
            return image
        else:
            return None

    def get_slideshow_images(self, obj):
        images = Image.active.get_images_for_news(obj.id)
        if images:
            final_images = ImageSerializer(instance=images, user=self.user, token=self.auth_token, many=True)
            final_images.include_fields(('id', 'title', 'description', 'url', 'image', 'auth_token', 'data_content_type'))
            return final_images.data
        else:
            return None

    def get_martini_image(self, obj):
        if obj.first_image:
            try:
                image = obj.first_image.version_generate('martini_image_400_200').url
            except Exception as exc:
                image = NoImage(path=get_no_image("martini")).image.version_generate('martini_image_400_200').url
            return image
        elif obj.first_video:
            return obj.first_video
        else:
            return None

   

class UcbrowserNewsSerializer(BaseNewsSerializer):
    language = serializers.SerializerMethodField()    
    publishTime = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    subcategory = serializers.SerializerMethodField()
    articleFrom = serializers.SerializerMethodField('get_article_source')
    coverPic = serializers.SerializerMethodField('get_cover_pic')
    originalUrl = serializers.SerializerMethodField('get_original_url')
    detailUrl = serializers.SerializerMethodField('get_detail_url')
    summary = serializers.SerializerMethodField('get_short_description')

    class Meta:
        model = News
        list_serializer_class = ListNewsSerializer
    
    def get_short_description(self,obj):
        return ""

    def get_original_url(self,obj):
        if obj.language == settings.HINDI_NEWS_TYPE:
            return settings.SCHEME+"://www.desimartini.com"+settings.PREFIX_HINDI_URL+obj.get_absolute_url() 
        else:            
            return settings.SCHEME+"://www.desimartini.com"+obj.get_absolute_url()    

    def get_detail_url(self,obj):
        if obj.language == settings.HINDI_NEWS_TYPE:
            return settings.SCHEME+"://m.desimartini.com"+settings.PREFIX_HINDI_URL+obj.get_ucb_url
        else:            
            return settings.SCHEME+"://m.desimartini.com"+obj.get_ucb_url   

    def get_language(self,obj):       
        return settings.NEWS_LANGUAGES[obj.language -1][1].lower()

    def get_description(self,obj):
        from BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(obj.content)
        [s.extract() for s in soup('script')]
        return soup.getText()[:200]
    
    def get_publishTime(self,obj):
        return obj.modified_date.strftime('%s')
    
    def get_category(self,obj):      
        return 'news'

    def get_subcategory(self,obj):
        if obj.category == settings.LIST_TYPE:
            return 'entertainment'            
        elif obj.category == settings.DM_EDITORIAL_TYPE:
            return 'movie'

    def get_article_source(self,obj):
        return 'Desimartini'

    def get_cover_pic(self,obj):
        image = obj.get_image()
        try:
            return [image.url]
        except:
            try:
                return [image.image.url]
            except AttributeError:
                return image     

class PaginatedUcBrowserSerializer(BasePaginationSerializer):
    class Meta:
        object_serializer_class = UcbrowserNewsSerializer


class PaginatedNewsSerializer(BasePaginationSerializer):
    """
    Serializes page objects of user querysets.
    """
    class Meta:
        object_serializer_class = NewsSerializer

class PaginatedLhNewsSerializer(BasePaginationSerializer):
    """
    Serializes page objects of user querysets.
    """
    class Meta:
        object_serializer_class = NewsLhSerializer
        

class RelatedNewsSerializer(BaseSerializer):
    related_news = serializers.SerializerMethodField()
    def get_related_news(self, obj):
        related_news = News.active.get_recent_news(obj)[:10]
        serializer = NewsSerializer(instance=related_news, many=True, image_type=self.image_type)
        serializer.include_fields(('id', 'title', 'short_text', 'url', 'first_video', 'first_image', 'created_date', 'data_content_type', 'category' , 'modified_date'))
        return serializer.data

class EntityNewsSerializer(BaseSerializer):
    news_info = serializers.SerializerMethodField()
    class Meta:
        model = RelatedNews
        list_serializer_class = ListNewsSerializer
        fields = ('id','news_info')

    def get_news_info(self,obj):
        newsdata = NewsSerializer(obj.news, image_type=self.image_type)
        #newsdata.include_fields(('id','title','url','news_thumbnail','created_date','category','short_text','modified_date',))
        newsdata.include_fields(('id','title','url','modified_date','language','short_text','news_thumbnail'))
        return newsdata.data


class PaginatedEntityNewsSerializer(BasePaginationSerializer):
    """
    Serializes page objects of user querysets.
    """
    class Meta:
        object_serializer_class = EntityNewsSerializer
 
class NewsRelatedContentSerializer(serializers.Serializer):
    # related_news = serializers.SerializerMethodField()

    title = serializers.SerializerMethodField()
    absolute_url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_title(self, obj):
        
        if hasattr(obj.content_object,'title'):
            return obj.content_object.title

        if hasattr(obj.content_object,'name'):
            return obj.content_object.name



    def get_absolute_url(self, obj):
        if obj.content_object.__class__.__name__ == "External":
            return obj.content_object.url

        return obj.content_object.get_absolute_url()

    def get_image(self, obj):
        
        if obj.content_object.__class__.__name__ == "Movie":
            jsarea_image = obj.content_object.get_jsarea_image()
            if jsarea_image:
                image_url = settings.MEDIA_URL + jsarea_image.path

                return image_url

        elif obj.content_object.__class__.__name__ == "News":

            if hasattr(obj.content_object, 'martini_horizontal') and obj.content_object.martini_horizontal:
                # import pdb
                # pdb.set_trace()
                return settings.MEDIA_URL + obj.content_object.martini_horizontal.path
            elif hasattr(obj.content_object, 'first_image') and obj.content_object.first_image.__class__.__name__ == "FileObject":
                return obj.content_object.first_image.url
            return ""   

        elif obj.content_object.__class__.__name__ == "Celeb":
            return settings.MEDIA_URL + obj.content_object.get_gallery_image().image.path


        elif obj.content_object.__class__.__name__ == "Video":
            return "https://img.youtube.com/vi/"+ obj.content_object.video_youtube_id +"/mqdefault.jpg"

        elif obj.content_object.__class__.__name__ == "External":
            return obj.content_object.thumbnail.path
        
        return obj.content_object.get_cover_image().image.path

