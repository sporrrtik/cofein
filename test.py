items = [{'id': 1, "title": "Latte"}, {'id': 2, "title": "Frappe"}, {'id': 3, "title": "Frappe"}]
order = "1,1,2"
order = order.split(",")
slovar = {i['id']:0 for i in items}
print(slovar)
for i in order:
    for item in items:
        if item['id'] == int(i):
            print(item)
            break
