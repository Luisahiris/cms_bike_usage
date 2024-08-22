# Install Bokeh -> pip install bokeh
from bokeh.plotting import figure, curdoc
from bokeh.io import push_notebook, show, output_notebook
from bokeh.models import ColumnDataSource, FactorRange, Label, Div, CustomJS, Select
from bokeh.models.tools import HoverTool
from bokeh.palettes import GnBu4, OrRd3
from bokeh.layouts import column, row, gridplot
import pandas as pd
from os.path import dirname, join
from functools import reduce

# ----------------------------- DATASETS -------------------------------------------------------
# 2017
csv_path_2017 = r"datasets\Citywide_Mobility_Survey_-_Main_2017_20240801.csv"
ds_2017 = pd.read_csv(csv_path_2017, low_memory=False)

# 2018
csv_path_2018 = r"datasets\Citywide_Mobility_Survey_-_Main_2018_20240801.csv"
ds_2018 = pd.read_csv(csv_path_2018, low_memory=False)

# 2019
csv_path_2019 = r"datasets\Citywide_Mobility_Survey_-_Person_2019_20240801.csv"
ds_2019 = pd.read_csv(csv_path_2019, low_memory=False)

# 2020
csv_path_2020 = r"datasets\Citywide_Mobility_Survey_-_October_2020_20240801.csv"
ds_2020 = pd.read_csv(csv_path_2020, low_memory=False)

# 2022
csv_path_2022 = r"datasets\Citywide_Mobility_Survey_-_Person_2022_20240725.csv"
ds_2022 = pd.read_csv(csv_path_2022, low_memory=False)

# ------------------------------ CODEBOOKS -----------------------------------------------------
# 2017 codebook
csv_path_codebook_2017 = r"codebooks\Data_Dictionary_-Citywide_Mobility_Survey_Main_2017.xlsx"
codebook_2017 = pd.read_excel(csv_path_codebook_2017, sheet_name="Column Info", index_col=[0])
codebook_2017 = codebook_2017.reset_index()
codebook_2017.columns = ["column_name", "column_description", "qnumber", "additional_notes"]

# 2018 codebook
csv_path_codebook_2018 = r"codebooks\Open_Data_Dictionary_Main_Survey_2018.xlsx"
codebook_2018 = pd.read_excel(csv_path_codebook_2018, sheet_name="Column Info")
codebook_2018.columns = ["column_name", "column_description", "qnumber", "additional_notes"]

# 2019 codebook
csv_path_codebook_2019 = r"codebooks\Data-Dictionary-Citywide_Mobility_Survey_-_Person_Survey_2019.xlsx"
codebook_2019 = pd.read_excel(csv_path_codebook_2019, sheet_name="Column Information")
codebook_2019.columns = ["column_name", "column_description", "values", "limitations", "additional_notes"]

# 2020 codebook
csv_path_codebook_2020 = r"codebooks\Data-Dictionary-Citywide_Mobility_Survey_-_October_2020.xlsx"
codebook_2020 = pd.read_excel(csv_path_codebook_2020, sheet_name="Column Information")
codebook_2020.columns = ["column_name", "column_description", "values", "limitations", "additional_notes"]

# 2022 codebook
csv_path_codebook_2022 = r"codebooks\2022_NYC_CMS_Codebook.xlsx"
codebook_2022 = pd.read_excel(csv_path_codebook_2022, sheet_name="value_labels")

# ------------------------------------------------------------------------------------------------

# bike frequency
bf_2017 = ds_2017.filter(items=["qgender", "qbikeride", "allwt"])
bf_2018 = ds_2018.filter(items=["qGENDER", "qBIKERIDE", "allwt"]) # no need codebook
bf_2019 = ds_2019.filter(items=["gender", "bike_freq", "weight"])
bf_2020 = ds_2020.filter(items=["gender_cms", "bike_freq", "weight"])
bf_2022 = ds_2022.filter(items=["gender", "bike_freq", "person_weight"]) 

def decoder(codebk, dataset, key, divider = '='):
  categories_list = {}
  for col in dataset.columns:
    if col == "allwt" or col == "weight":
      continue
    categories = codebk[codebk["column_name"] == col].filter(items=[key])
    categories = categories.iloc[0][key].split('\n')
    values = []
    labels = []
    for ele in categories:
      index = ele.find(divider)
      values.append(int(ele[:index]))
      labels.append(ele[index+1:].strip())

    categories_list[col] = pd.DataFrame({
      'value': values,
      'label': labels
    })
    
  return categories_list

# categories
# 2017
categories_list_2017 = {}
for col in bf_2017.columns:
  if col == "allwt":
    continue
  categories = codebook_2017[codebook_2017["column_name"] == col].filter(items=["additional_notes"])

  values = []
  labels = []
  for ele in categories["additional_notes"]:
    index = ele.find('=')
    values.append(int(ele[:index]))
    labels.append(ele[index+1:].strip())
    
  categories_list_2017[col] = pd.DataFrame({
    'value': values,
    'label': labels
  })
  
# 2019
categories_list_2019 = decoder(codebook_2019, bf_2019, "values", ':')

# 2020
categories_list_2020 = decoder(codebook_2020, bf_2020, "values", '-')

# 2022
categories_list_2022 = {}
for col in bf_2022.columns:
  categories = codebook_2022[codebook_2022["variable"] == col].filter(items=["value", "label"])
  categories_list_2022[col] = categories


def coder(dataset, categories_list):
  coded_df = pd.DataFrame.copy(dataset)
  for col in dataset.columns:
    if col == "person_weight" or col == "allwt" or col == "weight":
      continue
    categories = categories_list[col]
    column_values = dataset[col] # get uncoded values
    new_values = []
    for x in column_values:
        values = categories[categories["value"] == x].values
        if not values.any():
          new_values.append(x)
        else: 
          new_values.append(categories[categories["value"] == x].values[0][1])
    coded_df[f"{col}_value"] = new_values
  return coded_df

# 2017
coded_bf_2017 = coder(bf_2017, categories_list_2017)

# 2019
coded_bf_2019 = coder(bf_2019, categories_list_2019)

# 2020
coded_bf_2020 = coder(bf_2020, categories_list_2020)

# 2022
coded_bf_2022 = pd.DataFrame.copy(bf_2022)
new_col = {}
for col in bf_2022.columns:
  if col == "person_weight":
    continue
  categories = categories_list_2022[col]
  labels = categories["label"]
  column_values = bf_2022[col]
  new_values = []
  for x in column_values:
    values = categories[categories["value"] == x].values
    if not values.any():
      new_values.append(x)
    else:
      new_values.append(categories[categories["value"] == x].values[0][1])
        
  new_col[f"{col}_value"] = new_values

for col in new_col:
  coded_bf_2022[col] = new_col[col]

# Plot ranges
bike_freq_values_2017 = categories_list_2017["qbikeride"]["label"].tolist()
gender_values_2017 = categories_list_2017["qgender"]["label"].tolist()


dismiss = ["Don’t know", "Refused", "Don't know", 'Physically unable to ride a bike', 'Never']
gender_values_2017 = [ele for ele in gender_values_2017 if ele in ['Female', 'Male']]
bike_freq_values_2017 = [ele for ele in bike_freq_values_2017 if ele not in dismiss]

print(bike_freq_values_2017)
print(gender_values_2017)

gender_grouped = {}
gender_grouped['2017'] = coded_bf_2017.groupby(["qgender_value", "qbikeride_value"])["allwt"]
gender_grouped['2018'] = bf_2018.groupby(["qGENDER", "qBIKERIDE"])["allwt"]
gender_grouped['2019'] = coded_bf_2019.groupby(["gender_value", "bike_freq_value"])["weight"]
gender_grouped['2020'] = coded_bf_2020.groupby(["gender_cms_value", "bike_freq_value"])["weight"]
gender_grouped['2022'] = coded_bf_2022.groupby(["gender_value", "bike_freq_value"])["person_weight"]

alternatives_bf_2022 = {
  'Once a week or more': ['5 or more days a week', 
                          '4 days a week', 
                          '2-3 days a week'],
  'Several times a month': ['1 day a week'],
  'At least once a month': ['1-3 days a month'],
  'A few times a year': ['Less than monthly'],
  'Never': ['Never'],
}

alternative_gender_2022 = {
    'Male': 'Man',
    'Female': 'Woman'
}

def handle_2022(gd, freq):
  count = 0
  alter_arr = alternatives_bf_2022[freq]
  gender = alternative_gender_2022[gd]
  for alter_freq in alter_arr:
    try:
      val = gender_grouped['2022'].get_group((gender, alter_freq)).agg(["sum", "count"])
      count += val["count"]
    except:
      count = count
  return {'count': count}

df = {
    'group': []
}

for year in ['2017', '2018', '2019', '2020', '2022']:
  for gender_val in gender_values_2017:
    df['group'].append((year, gender_val))
    for freq in bike_freq_values_2017:
      try:
        arr = df[freq]
      except:
        df[freq] = []

      try:
        if year == '2022':
          val = handle_2022(gender_val, freq)
        else:
          val = gender_grouped[year].get_group((gender_val, freq)).agg(["sum", "count"])
      except:
          val = {
            'count': 0
          }
      df[freq].append(val["count"])


totals = []
for i in range(10):
  count = 0
  for key in df:
    if key == "group":
      continue
    count += df[key][i]
  totals.append(count)
  
  
# ---------------------- PLOTTING -----------------------------------------------------
desc = Div(text=open(join(dirname(__file__), "header.html")).read(), margin=(0,0,0,400))

def create_widget(year, f_index, m_index):
  f_text = round(totals[f_index])
  m_text = round(totals[m_index])
  
  widget = figure(x_range=(0,10), height=100, width=200, y_range=(0, 10), title="",
            toolbar_location=None, x_axis_location=None, y_axis_location=None, css_classes=["widget"], margin=(0,15,20,0))

  label_year = Label(x=3, y=0.5, text=str(year), text_font_size='35px', text_color='#5044B8')
  label_total_f = Label(x=1.5, y=6, text=str(f_text), text_font_size='25px', text_color='#18780B')
  label_f = Label(x=1.4, y=4, text="FEMALE", text_font_size='10px', text_color='#2e484c')
  label_total_m = Label(x=6, y=6, text=str(m_text), text_font_size='25px', text_color='#500B78')
  label_m = Label(x=6.5, y=4, text="MALE", text_font_size='10px', text_color='#2e484c')

  widget.add_layout(label_total_m)
  widget.add_layout(label_total_f)
  widget.add_layout(label_m)
  widget.add_layout(label_f)
  widget.add_layout(label_year)

  widget.ygrid.grid_line_color = None
  widget.xgrid.grid_line_color = None
  
  return widget

widget2017 = create_widget(2017, 1, 0)
widget2018 = create_widget(2018, 3, 2)
widget2019 = create_widget(2019, 5, 4)
widget2020 = create_widget(2020, 7, 6)
widget2022 = create_widget(2022, 9, 8)

widget2017.margin = (0,15,20,400)

# -------------------------
def normalize_df(arr):
  norm_arr = []
  norm_arr.append(((arr[0] + arr[1])/(totals[0] + totals[1]))*100)
  norm_arr.append(((arr[2] + arr[3])/(totals[2] + totals[3]))*100)
  norm_arr.append(((arr[4] + arr[5])/(totals[4] + totals[5]))*100)
  norm_arr.append(((arr[6] + arr[7])/(totals[6] + totals[7]))*100)
  norm_arr.append(((arr[8] + arr[9])/(totals[8] + totals[9]))*100)
  
  return norm_arr

# dict_helper = {}
# for i in range(10):
#   array = []
#   for key in df:
#     if key == "group":
#       continue
#     array.append(df[key][i])
  
#   dict_helper[i] = array

norm_df = {}
for key in df:
  if key == 'group':
    norm_df[key] = ['2017', '2018', '2019', '2020', '2022']
    continue
  norm_df[key] = normalize_df(df[key])

print(norm_df)
  
norm_p = figure(y_range=norm_df['group'], height=350, x_range=(0, 100), title="Bike Frequency by Year (Normalized)",
           toolbar_location="above", tools="hover", tooltips="@group $name: @$name{0,0.000} %", margin=(0,0,0,200))

norm_renderers = norm_p.hbar_stack(bike_freq_values_2017, y='group', height=0.9, color=GnBu4, source=ColumnDataSource(norm_df))


norm_p.y_range.range_padding = 0.1
norm_p.ygrid.grid_line_color = None
# norm_p.legend.location = None

    
# -----------------------

ls_gender = ['Male', 'Female']
years_i = {'2017': 0, '2018': 2, '2019': 4, '2020': 6, '2022': 8}

def get_df(year):
  g_df = {
    'gender': ls_gender,
  }
  
  for key in df:
    if key == 'group':
      continue
    
    g_df[key] = [df[key][years_i[year]], df[key][years_i[year]+1]]
    
  return g_df

gender_df = ColumnDataSource(get_df('2022'))

def update_df(att, old, new):
  gender_df.data = get_df(new)
  # p_gender.source = ColumnDataSource(gender_df)

p_gender = figure(x_range=ls_gender, height=350, y_range=(0, 650), title="Bike Frequency by Gender",
           toolbar_location="right")

r_gender = p_gender.vbar_stack(bike_freq_values_2017, x='gender', width=0.9, color=GnBu4, source=gender_df,
             legend_label=[f"{freq}" for freq in bike_freq_values_2017])

# p.hbar_stack(years, y='fruits', height=0.9, color=OrRd3, source=ColumnDataSource(imports),
#              legend_label=[f"{year} imports" for year in years])

p_gender.x_range.range_padding = 0.1
p_gender.xgrid.grid_line_color = None
p_gender.legend.location = "top_left"
# p.legend.orientation = "horizontal"
p_gender.add_layout(p_gender.legend[0], 'left')
# p.legend.ncols = 2
# p.axis.minor_tick_line_color = None
# p.outline_line_color = None

for r in r_gender:
    freq = r.name
#     index = r["$index"]
#     total = str(totals["$index"])
    g_hover = HoverTool(tooltips=[
#         ("Percentage", str(totals["$index"])),
        ("Bike_freq", freq),
        ("Count", " @$name"),
        ("Gender", " @gender"),
        ("index", "$index")
    ], renderers=[r])
    p_gender.add_tools(g_hover)
    
# ------------------------
#Dropdown

select = Select(title="Select year:", value="2022", options=["2022", "2020", "2019", "2018", "2017"])
select.on_change('value', update_df)
    
# -------------------------

p = figure(x_range=FactorRange(*df['group']), height=350, width=1500, y_range=(0, 650), title="Bike Frequency by Gender and Year",
           toolbar_location="above", margin=(0, 0, 0, 200))

renderers = p.vbar_stack(bike_freq_values_2017, x='group', width=0.9, color=GnBu4, source=ColumnDataSource(df),
             legend_label=[f"{freq}" for freq in bike_freq_values_2017])

# p.hbar_stack(years, y='fruits', height=0.9, color=OrRd3, source=ColumnDataSource(imports),
#              legend_label=[f"{year} imports" for year in years])

p.x_range.range_padding = 0.1
p.xgrid.grid_line_color = None
p.legend.location = "top_left"
p.add_layout(p.legend[0], 'right')

for r in renderers:
    freq = r.name
    hover = HoverTool(tooltips=[
        ("Bike_freq", freq),
        ("Count", " @$name"),
        ("Year, Gender", " @group"),
    ], renderers=[r])
    p.add_tools(hover)

layout = column(desc, row(widget2017, widget2018, widget2019, widget2020, widget2022), row(norm_p, p_gender, select), p)
curdoc().add_root(layout)
curdoc().title = "CMS Bike Frequency"
