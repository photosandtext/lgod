from django.contrib import admin
from app.models import Article, Category, FileUpload, ArticleImage

class ArticleAdmin(admin.ModelAdmin):
    pass

class CategoryAdmin(admin.ModelAdmin):
    pass

class FileAdmin(admin.ModelAdmin):
    pass

class ArticleImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(FileUpload, FileAdmin)
admin.site.register(ArticleImage, ArticleImageAdmin)

