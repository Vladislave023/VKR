from django.http import JsonResponse
from .models import Department, Program

def departments_by_institute(request):
    institute_id = request.GET.get("institute_id")
    if not institute_id:
        return JsonResponse({"results": []})

    qs = Department.objects.filter(institute_id=institute_id).order_by("name")
    return JsonResponse({
        "results": [{"id": d.id, "name": d.name} for d in qs]
    })

def specialties_by_institute_and_level(request):
    institute_id = request.GET.get("institute_id")
    level_id = request.GET.get("education_level_id")
    if not institute_id or not level_id:
        return JsonResponse({"results": []})

    qs = (Program.objects
          .filter(institute_id=institute_id, education_level_id=level_id)
          .select_related("specialty")
          .order_by("specialty__code"))

    # уникальные направления (на случай дублей)
    seen = set()
    results = []
    for p in qs:
        if p.specialty_id in seen:
            continue
        seen.add(p.specialty_id)
        results.append({
            "id": p.specialty_id,
            "label": str(p.specialty),
        })

    return JsonResponse({"results": results})