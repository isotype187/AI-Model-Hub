import tkinter as tk
from core.catalog import sync_catalog, get_catalog
from core.recommender import recommend
import traceback

app = tk.Tk()
app.title('Refresh Test')
app.geometry('500x300')

print('BEFORE REFRESH')

try:
    sync_catalog()
    print('SYNC OK')

    data = get_catalog()
    print('CATALOG OK', len(data))

    result = recommend(data)
    print('RECOMMEND OK', len(result))

except Exception:
    traceback.print_exc()

print('START LOOP')
app.mainloop()
