from django import template

register = template.Library()

# custom filter to calculate total cost (quantity * price) and format it to two decimals
@register.filter(name='get_cost')
def get_cost(quantity, price):
    return "{:.2f}".format(quantity * price)

# custom filter to calculate the percentage of stock available (current quantity / total units * 100)
@register.filter(name='get_stock')
def get_stock(item):
    return item.curr_quantity/item.total_units * 100