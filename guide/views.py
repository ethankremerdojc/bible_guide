from django.shortcuts import render

# Create your views here.#

def guide_page(request, *args, **kwargs):
    return render(request, "guide/guide_page.html", context={})
