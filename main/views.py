from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
from RouteFinder import RF, AirportNotFound


# Create your views here.


def main(request):
    return render(request, 'index.html')


def get_route(request):
    rf = RF()
    if request.method == "POST":
        req = request.POST
        try:
            rf.input_info(req.get('dep'), req.get('arr'))
        except AirportNotFound as e:
            return JsonResponse({'error': str(e)})
        try:
            path = rf.find_path()
        except KeyError:
            return JsonResponse({'error': 'Route not found'})

        distance = rf.get_distance()
        path = {
            "distance": int(distance),
            "wpts": path,
            "route": rf.filter_route(),
            'from': rf.get_from(),
            'to': rf.get_to()
        }
        return JsonResponse(path, safe=False)
    # return HttpResponse('Hello world')


def airport_data(request):
    return render(request, 'airport_data.html')


def autocomplete(request):
    url = f' https://places.aviasales.ru/v2/places.json?locale=en&max=7&term={request.GET.get("term")}&types[]=city&types[]=airport'
    req = requests.get(url=url)
    res = req.json()
    res1 = []
    for i in res:
        if i.get('main_airport_name') or i['type'] == 'airport':
            res1.append({
                'label': f"{i['name']}{', ' + i['city_name'] if i.get('city_name') else ''}{', ' + i['country_name']}{', ' + i['code']}",
                'value': i['code']
            })
    return JsonResponse(res1, safe=False)


def autocomplete_icao(request):
    head = {'Authorization': f'Token ASZtHjzIsCzdOG--WkML2RlP-QLre9VKCXpLFWu1WIA'}
    url = f"https://avwx.rest/api/search/station?text={request.GET.get('term')}&airport=true"
    req = requests.get(url=url, headers=head)
    res = req.json()
    res1 = []
    for i in res:
        if i.get('icao'):
            res1.append({
                'label': f"{i['name']}{', ' + i['icao']}",
                'value': i['icao']
            })
    return JsonResponse(res1, safe=False)


def find_airport(request):
    head = {'Authorization': f'Token ASZtHjzIsCzdOG--WkML2RlP-QLre9VKCXpLFWu1WIA'}
    url = f"https://avwx.rest/api/station/{request.GET.get('apt')}"
    req = requests.get(url=url, headers=head)
    res = req.json()
    return render(request, 'find_airport.html', {'res': res})


def find_metar_taf(request):
    head = {'Authorization': f'Token ASZtHjzIsCzdOG--WkML2RlP-QLre9VKCXpLFWu1WIA'}
    url = f"https://avwx.rest/api/metar/{request.GET.get('apt')}"
    req = requests.get(url=url, headers=head)
    metar = req.json()
    url = f"https://avwx.rest/api/taf/{request.GET.get('apt')}"
    req = requests.get(url=url, headers=head)
    taf = req.json()
    return render(request, 'find_metar_taf.html', {'metar': metar,'taf':taf})


def metar_taf(request):
    metar = None
    taf = None
    if request.GET.get('apt'):
        head = {'Authorization': f'Token ASZtHjzIsCzdOG--WkML2RlP-QLre9VKCXpLFWu1WIA'}
        url = f"https://avwx.rest/api/metar/{request.GET.get('apt')}"
        req = requests.get(url=url, headers=head)
        metar = req.json()
        url = f"https://avwx.rest/api/taf/{request.GET.get('apt')}"
        req = requests.get(url=url, headers=head)
        taf = req.json()
    return render(request, 'metar_taf.html',{'metar': metar,'taf':taf} )


def nats(request):
    import requests
    from bs4 import BeautifulSoup
    url = "https://www.notams.faa.gov/common/nat.html"
    req = requests.get(url=url)
    soup = BeautifulSoup(req.text, 'html.parser')
    body = soup.select_one('body')
    fnd = body.find('table', {'width':'584'})
    fnd['width'] = ""
    fnd['border'] = 0
    return render(request, 'nats.html',{'table':str(body)})