# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import datetime
import json
import logging
from app.models import *

logger = logging.getLogger(__name__)

def home(request):
    user = request.user
    articles = get_list_or_404(Article.objects.filter(is_posted=True).order_by("-date_posted"))
    features = Article.objects.filter(is_posted=True,type='featured').order_by("-date_posted")[:10]
    paginator = Paginator(articles, 10)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, user=user)
    return render_to_response("home.html", d)

def category(request, jslug):
    user = request.user
    articles = get_list_or_404(Article.objects.filter(categories__slug=jslug, is_posted=True).order_by("-date_posted"))
    paginator = Paginator(articles, 10)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, features=features, user=user)
    return render_to_response("home.html", d)
    
def authorPage(request, jslug):
    social = None
    user = request.user
    staff = get_object_or_404(User, username__iexact=str(jslug))
    articles = get_list_or_404(Article.objects.filter(author__iexact=jslug, is_posted=True).order_by("-date_posted"))
    
    try: staffProfile = StaffProfile.objects.get(user=User.objects.get(username=jslug))
    except: staffProfile = None
    
    if staffProfile.twitter or staffProfile.facebook or staffProfile.gplus:
        social = 'social'

    paginator = Paginator(articles, 10)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, staff=staff, staffProfile=staffProfile, social=social, user=user)
    return render_to_response("authorPage.html", d)
    
def article(request, article_id, type):
    user = request.user
    posted = None
    pagetype = 'article'
    
    if type=='editorPreview' and request.user.is_authenticated():
        article = get_object_or_404(Article, id=article_id)
    else:
        article = get_object_or_404(Article, title_slug=str(article_id), is_posted=True)
    
    if article.is_posted:
        posted = 'posted'
    
    d = dict(user=user,article=article, posted=posted, pagetype=pagetype)
    return render_to_response("article.html", d)

@login_required
def articleEditor(request, article_id):
    user = request.user
    posted = None
    article = None
    if article_id is not None:
        article = get_object_or_404(Article, pk=article_id)
        if article.is_posted:
            posted = 'posted'

    if request.method == 'POST':
        if "discard_article" in request.POST:
            return HttpResponseRedirect('/staff')
        else:
            form = ArticleForm(request.POST, request.FILES, instance=article)
            if form.is_valid():
                article = form.save(commit=False)
                if "post_article" in request.POST:
                    now = datetime.datetime.now()
                    article.date_posted = now.strftime("%Y-%m-%dT%H:%M:%S")
                    article.is_posted = True
                    article.author = user
                elif "unpost_article" in request.POST:
                    article.is_posted = False
                article.edit_user = user
                article.save()
                form.save_m2m()
                return HttpResponseRedirect('/article/'+article.title_slug)
            
    else:
        form = ArticleForm(instance=article)

    return render_to_response("editor.html", {
        'form': form,
        'article' : article,
        'posted' : posted,
        'user' : user},
        context_instance=RequestContext(request))

@login_required
def imageEditor(request,article_id):
    article = get_object_or_404(Article, id=article_id)
    header, created = ArticleImage.objects.get_or_create(article = article, type='header')
    featured, created = ArticleImage.objects.get_or_create(article = article, type='featured')
    thumbnail, created = ArticleImage.objects.get_or_create(article = article, type='thumbnail')
    formset = imageFormset(queryset=ArticleImage.objects.filter(article=article.id))

    if request.method == "POST":
        formset = imageFormset(request.POST)
        if formset.is_valid():
            formset.save()

    return render_to_response("imageEditor.html", {
        'formset': formset,
        'article': article},
        context_instance=RequestContext(request))

@csrf_exempt
@require_POST
@login_required
def fileUpload(request):
    files = []
    for f in request.FILES.getlist("file"):
        obj = FileUpload.objects.create(file=f)
        obj.folder = 'Article Uploads'
        obj.save()
        files.append({"filelink": obj.cdn_url})
        logger.info(json.dumps(files))
    return HttpResponse(json.dumps(files), mimetype="application/json")

@csrf_exempt
@require_POST
@login_required
def fileUpdate(request):
    status = []
    file = FileUpload.objects.get(pk=request.POST['id'])
    file.title = request.POST['title']
    file.folder = request.POST['folder']
    file.save()
    status.append({'status':'saved'})
    return HttpResponse(json.dumps(status), mimetype="application/json")


@login_required
def recentFiles(request):
    files = [
        {"thumb": obj.cdn_url, "image": obj.cdn_url, "folder": obj.folder}
        for obj in FileUpload.objects.all().order_by("-uploaded")[:20]
        ]
    return HttpResponse(json.dumps(files), mimetype="application/json")    
        
@login_required
def staffHome(request):
    user = request.user
    articles = get_list_or_404(Article.objects.all().order_by("-date_posted"))
    paginator = Paginator(articles, 30)

    try: page = int(request.GET.get("page", '1'))
    except ValueError: page = 1

    try: articles = paginator.page(page)
    except (InvalidPage, EmptyPage):
        articles = paginator.page(paginator.num_pages)

    d = dict(articles=articles, user=user)
    return render_to_response("staffHome.html", d)

@login_required
def staffFileManager(request):
    filelist = FileUpload.objects.all()

    d = dict(filelist=filelist)
    return render_to_response("staffFileManager.html", d)

@login_required    
def profilePage(request):
    user = request.user
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    notice = None
    
    if request.method == "POST":
        uform = UserForm(request.POST, instance=request.user)
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid() and uform.is_valid():
            uform.save()
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            notice = "Saved!"
    
    else:
        form = ProfileForm(instance=profile)
        uform = UserForm(instance=request.user)
        
    return render_to_response("profile.html", {
        'form': form,
        'uform': uform,
        'notice': notice,
        'user': user},
        context_instance=RequestContext(request))