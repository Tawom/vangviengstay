from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from tours.models import Tour
from guesthouse.models import Guesthouse
from motorbike.models import Motorbike
from buggy.models import BuggyCar
from guides.models import Guide


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Add the names of your main list views here
        return ['guesthouse_list', 'tour_list', 'motorbike_list', 'buggy_list', 'guide_list']

    def location(self, item):
        return reverse(item)


class TourSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Tour.objects.filter(is_active=True)

    def location(self, obj):
        return f"/tours/{obj.id}/"


class GuesthouseSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Guesthouse.objects.filter(is_active=True)

    def location(self, obj):
        return f"/guesthouses/{obj.id}/"


class MotorbikeSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Motorbike.objects.filter(is_active=True)

    def location(self, obj):
        return f"/motorbikes/{obj.id}/"


class BuggySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return BuggyCar.objects.filter(is_active=True)

    def location(self, obj):
        return f"/buggies/{obj.id}/"


class GuideSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Guide.objects.filter(is_active=True)

    def location(self, obj):
        return f"/guides/{obj.id}/"