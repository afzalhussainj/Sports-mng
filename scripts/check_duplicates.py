from core.models import TeamMember
from django.db.models import Count

print('Duplicate members:')
duplicates = TeamMember.objects.values('name').annotate(count=Count('id')).filter(count__gt=1)
for d in duplicates:
    print(f'{d["name"]}: {d["count"]} instances')
    members = TeamMember.objects.filter(name=d['name'])
    for m in members:
        print(f'  ID: {m.id}, Captain: {m.is_captain}')
