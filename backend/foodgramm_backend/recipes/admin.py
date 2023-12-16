from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (Recipe, Ingredient, Tag,
                     ShopCart, Best, IngredientRecipe)

admin.site.empty_value_display = 'Не задано'


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientRecipeInline, )
    list_display = ('recipe_image', 'name', 'author', 'ingr',)
    list_editable = ('name',)
    list_filter = ('author', 'name', 'tags')

    @admin.display(description='Картинка')
    def recipe_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">'
                         ) if obj.image else None

    @admin.display(description='Ингредиенты')
    def ingr(self, obj):
        return list(obj.ingredients.values_list('name', flat=True))


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    list_display = ('recipe',)
    list_filter = ('user',)


@admin.register(Best)
class BestAdmin(admin.ModelAdmin):
    list_display = ('recipe',)
    list_filter = ('user',)


admin.site.site_title = 'Администрирование Фудграмм'
admin.site.site_header = 'Администрирование Фудграмм'
