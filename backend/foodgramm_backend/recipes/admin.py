from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Recipe, Ingredient, Tag

admin.site.empty_value_display = 'Не задано'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe_image', 'name', 'author', 'best',)
    list_editable = ('name',)
    list_filter = ('author', 'name', 'tags')

    @admin.display(description='Картинка')
    def recipe_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">'
                         ) if obj.image else None

    @admin.display(description='В избранном')
    def best(self, obj):
        return obj.favorited.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


admin.site.site_title = 'Администрирование Фудграмм'
admin.site.site_header = 'Администрирование Фудграмм'
