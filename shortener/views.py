from django.db.models import F
from django.conf import settings
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from shortener.baseconv import base62
from shortener.models import Link
from shortener.forms import LinkSubmitForm

short_url = getattr(settings, "SHORTENING_DOMAIN", None)
short_scheme = getattr(settings, "SHORTENING_SCHEME", None)
@csrf_exempt
@require_GET
def follow(request, base62_id):
    """
    View which gets the link for the given base62_id value
    and redirects to it.
    """
    link = get_object_or_404(Link, id=base62.to_decimal(base62_id))
    link.usage_count = F('usage_count') + 1
    link.save()
    return HttpResponsePermanentRedirect(link.url)

@csrf_exempt
@require_GET
def info(request, base62_id):
    """
    View which shows information on a particular link
    """
    link = get_object_or_404(Link, id=base62.to_decimal(base62_id))
    return JsonResponse({'short_url': "/".join(["://".join([short_scheme or request.scheme,short_url or request.get_host()]),link.to_base62()]),
                        'url': link.url,
                        'follow_count':link.usage_count
                        })

@csrf_exempt
@require_POST
def submit(request):
    """
    View for submitting a URL to be shortened
    """
    form = LinkSubmitForm(request.POST)
    if form.is_valid():
        kwargs = {'url': form.cleaned_data['url']}
        custom = form.cleaned_data['custom']
        if custom:
            # specify an explicit id corresponding to the custom url
            kwargs.update({'id': base62.to_decimal(custom)})
        link = Link.objects.create(**kwargs)
        return JsonResponse({'short_url': "/".join(["://".join([short_scheme or request.scheme,short_url or request.get_host()]),link.to_base62()])},status=201)
    else:
        return JsonResponse({'errors': form.errors},status=400)

@csrf_exempt
@require_GET
def index(request):
    """
    View for main page
    """
    values = {
        'link_form': LinkSubmitForm(),
        'recent_links': Link.objects.all().order_by('-date_submitted')[:5],
        'most_popular_links': Link.objects.all().order_by('-usage_count')[:5]}
    return render(request, 'shortener/index.html', values)
