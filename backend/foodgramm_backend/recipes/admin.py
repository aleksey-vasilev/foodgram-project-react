from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Recipe, Ingredient

admin.site.empty_value_display = 'Не задано'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'recipe_image',
        'name',
        'author',
    )
    list_editable = (
        'name',
        'text',
    )
    search_fields = ('name',)
    list_filter = ('cooking_time',)

    @admin.display(description='Картинка')
    def recipe_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">'
                         ) if obj.image else None


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_editable = (
        'name',
        'measurement_unit',
    )


admin.site.site_title = 'Администрирование Фудграмм'
admin.site.site_header = 'Администрирование Фудграмм'
