from enum import Enum
import pandas as pd
import numpy as np

def clean_text(series):
    return series.astype('string').str.strip().str.lower()

morning = pd.read_csv('shift_morning_raw.csv', sep=';')
day = pd.read_csv('shift_day_raw.csv', sep=';')
night = pd.read_csv('shift_night_raw.csv', sep=',')



morning = morning.rename(columns={
    "date": "production_date",
    "product": "product_name",
    "operator": "operator_name",
    "produced": "produced_units",
    "defective": "defective_units",
    "temp_c": "storage_temperature_c",
    "status":"quality_status",
    "note" :"comment"
})

day = day.rename(columns={
'Партия': 'batch_id',
    'Дата производства': 'production_date',
    'Смена': 'shift',
    'Продукт': 'product_name',
    'Оператор': 'operator_name',
    'Произведено': 'produced_units',
    'Брак': 'defective_units',
    'Температура хранения': 'storage_temperature_c',
    'Статус качества': 'quality_status',
    'Комментарий': 'comment'
})

night = night.rename(columns={
'batch': 'batch_id',
    'prod_date': 'production_date',
    'shift_name': 'shift',
    'item': 'product_name',
    'units_produced': 'produced_units',
    'units_defective': 'defective_units',
    'storage_t': 'storage_temperature_c',
    'qc_status': 'quality_status',
    'comments': 'comment'
})


##print('Смены:', morning['shift'].unique(),
##      day['shift'].unique(), night['shift'].unique())

##print('Статусы:', morning['quality_status'].unique(),
##      day['quality_status'].unique(), night['quality_status'].unique())

##print('Продукты:', morning['product_name'].unique(),
##      day['product_name'].unique(), night['product_name'].unique())

shift_dict = {
    'утренняя': 'morning',
    'утро': 'morning',
    'утренняя смена': 'morning',
    'morning': 'morning',
    'day': 'day',
    'дневная': 'day',
    'день': 'day',
    'night': 'night',
    'ночь': 'night',
    'ночная': 'night'
}

status_dict = {
    'годна': 'passed',
    'годен': 'passed',
    'ok': 'passed',
    'ок': 'passed',
    'passed': 'passed',

    'повторный контроль': 'review',
    'review': 'review',
    'на проверке': 'review'
}

product_dict = {
    # Йогурт «Черника» 2,5%
    'йогурт «черника» 2,5%': 'Йогурт «Черника» 2,5%',
    'йогурт черника 2.5%': 'Йогурт «Черника» 2,5%',
    'йогурт черника 2,5%': 'Йогурт «Черника» 2,5%',

    # Йогурт натуральный 3,2%
    'йогурт натуральный 3,2%': 'Йогурт натуральный 3,2%',
    'йогурт натуральный 3.2%': 'Йогурт натуральный 3,2%',
    'йогурт натуральный': 'Йогурт натуральный 3,2%',

    # Биойогурт «Мягкий» 1%
    'биойогурт «мягкий» 1%': 'Биойогурт «Мягкий» 1%',
    'биойогурт мягкий 1.0%': 'Биойогурт «Мягкий» 1%',
    'биойогурт мягкий 1%': 'Биойогурт «Мягкий» 1%',

    # Йогурт «Клубника» 2,5%
    'йогурт клубника 2.5%': 'Йогурт «Клубника» 2,5%',
    'йогурт «клубника» 2,5%': 'Йогурт «Клубника» 2,5%',
    'йогурт клубника 2,5%': 'Йогурт «Клубника» 2,5%',

    # Йогурт натуральный — остальные варианты уже выше
}

for df in [morning, day, night]:

    df['shift'] = clean_text(df['shift']).map(shift_dict)

    df['quality_status'] = (
        clean_text(df['quality_status']).map(status_dict)
    )

    df['product_name'] = (
        clean_text(df['product_name']).map(product_dict)
    )



raw_morning = pd.read_csv('shift_morning_raw.csv', sep=';')
raw_day = pd.read_csv('shift_day_raw.csv', sep=';')
raw_night = pd.read_csv('shift_night_raw.csv', sep=',')

# Сохраняем исходные номера строк
morning['_source_row'] = morning.index
day['_source_row'] = day.index
night['_source_row'] = night.index

morning['source_file'] = 'shift_morning_raw.csv'
day['source_file'] = 'shift_day_raw.csv'
night['source_file'] = 'shift_night_raw.csv'

data = pd.concat(
    [morning, day, night],
    ignore_index=True
)

data['production_date'] = pd.to_datetime(
    data['production_date'],
    format='mixed',
    dayfirst=True,
    errors='coerce'
)
numeric_columns = [
    'produced_units',
    'defective_units',
    'storage_temperature_c'
]
for col in numeric_columns:
    data[f'_raw_{col}'] = data[col].copy()

def clean_number(series):
    return pd.to_numeric(
        series.astype('string')
        .str.replace(r'[^\d,.\-]', '', regex=True)
        .str.replace(',', '.', regex=False),
        errors='coerce'
    )


for col in numeric_columns:
    data[col] = clean_number(data[col])

data['batch_id'] = (
    data['batch_id']
    .astype('string')
    .str.strip()
    .str.upper()
)

check_columns = [
    col for col in data.columns
    if col != '_source_row'
]

duplicates = data[
    data.duplicated(subset=check_columns, keep='first')
].copy()


data = data.drop_duplicates(
    subset=check_columns,
    keep='first'
).copy()

suspicious_conditions = {
    'negative_defective': data['defective_units'] < 0,

    'defective_exceeds_produced':
        data['defective_units'] > data['produced_units'],

    'excessive_production':
        data['produced_units'] > 100000,

    'missing_production':
        data['produced_units'].isna(),

    'suspicious_temperature':
        data['storage_temperature_c'] > 15,

    'unknown_status':
        data['quality_status'].isna()
}

suspicious_mask = pd.Series(False, index=data.index)

for condition in suspicious_conditions.values():
    suspicious_mask |= condition.fillna(False)


suspicious_data = data.loc[suspicious_mask].copy()
raw_files = {
    'shift_morning_raw.csv': raw_morning,
    'shift_day_raw.csv': raw_day,
    'shift_night_raw.csv': raw_night
}

suspicious_original = []

for filename, raw_df in raw_files.items():

    rows = suspicious_data.loc[
        suspicious_data['source_file'] == filename,
        '_source_row'
    ]

    original_rows = raw_df.loc[rows].copy()
    original_rows['source_file'] = filename

    suspicious_original.append(original_rows)

suspicious_rows = pd.concat(
    suspicious_original,
    ignore_index=True,
    sort=False
)
suspicious_rows.to_csv(
    'suspicious_rows.csv',
    index=False,
    encoding='utf-8-sig'
)


factory = data.loc[~suspicious_mask].copy()

factory['defect_rate'] = (
    factory['defective_units'] / factory['produced_units']
)
factory['good_units'] = (
    factory['produced_units'] - factory['defective_units']
)
factory['temperature_status'] = np.select(
    [
        factory['storage_temperature_c'].isna().to_numpy(),
        (factory['storage_temperature_c'] > 8).fillna(False).to_numpy()
    ],
    [
        'unknown',
        'risk'
    ],
    default='normal'
)
# Формат номера партии
factory['batch_id'] = factory['batch_id'].str.replace(
    r'^B-(\d+)$',
    lambda m: 'B-' + m.group(1).zfill(4),
    regex=True
)

# Числа без десятичных знаков
factory['produced_units'] = factory['produced_units'].astype('int64')
factory['defective_units'] = factory['defective_units'].astype('int64')
factory['good_units'] = factory['good_units'].astype('int64')

# Формат даты
factory['production_date'] = (
    factory['production_date'].dt.strftime('%Y-%m-%d')
)

factory = factory.drop(
    columns=[
        '_source_row',
        'source_file',
        '_raw_produced_units',
        '_raw_defective_units',
        '_raw_storage_temperature_c'
    ]
)

factory = factory[[
    'batch_id',
    'production_date',
    'shift',
    'product_name',
    'operator_name',
    'produced_units',
    'defective_units',
    'storage_temperature_c',
    'quality_status',
    'comment',
    'defect_rate',
    'good_units',
    'temperature_status'
]]

factory.to_csv(
    'factory.csv',
    index=False,
    encoding='utf-8-sig'
)


report = []

def add_report(issue_type, source_file, column_name, rows_count, action):
    if rows_count > 0:
        report.append({
            'issue_type': issue_type,
            'source_file': source_file,
            'column_name': column_name,
            'rows_count': int(rows_count),
            'action': action
        })

for filename in raw_files:

    count = (duplicates['source_file'] == filename).sum()

    add_report(
        'duplicate_rows',
        filename,
        'all',
        count,
        'removed'
    )

for filename in raw_files:

    source_data = data[data['source_file'] == filename]

    for col in numeric_columns:

        raw_col = source_data[f'_raw_{col}'].astype('string')

        changed = raw_col.str.contains(
            r'[,]|[^0-9.\-\s]',
            regex=True,
            na=False
        )

        add_report(
            'invalid_number',
            filename,
            col,
            changed.sum(),
            'cleaned'
        )

issue_columns = {
    'negative_defective': 'defective_units',
    'defective_exceeds_produced': 'defective_units',
    'excessive_production': 'produced_units',
    'missing_production': 'produced_units',
    'suspicious_temperature': 'storage_temperature_c',
    'unknown_status': 'quality_status'
}

for issue, condition in suspicious_conditions.items():

    for filename in raw_files:

        mask = (
            condition &
            (data['source_file'] == filename)
        )

        add_report(
            issue,
            filename,
            issue_columns[issue],
            mask.sum(),
            'moved_to_suspicious'
        )

for filename in raw_files:

    count = (
        data.loc[data['source_file'] == filename,
                 'storage_temperature_c'].isna()
    ).sum()

    add_report(
        'missing_temperature',
        filename,
        'storage_temperature_c',
        count,
        'kept_as_unknown'
    )

report_df = pd.DataFrame(report)

report_df.to_csv(
    'data_quality_report.csv',
    index=False,
    encoding='utf-8-sig'
)

original_count = (
    len(raw_morning) +
    len(raw_day) +
    len(raw_night)
)

factory_count = len(factory)
suspicious_count = len(suspicious_rows)
duplicates_count = len(duplicates)




shift_analysis = factory.groupby('shift').agg(
    produced=('produced_units', 'sum'),
    defective=('defective_units', 'sum')
)

shift_analysis['defect_rate'] = (
    shift_analysis['defective'] / shift_analysis['produced']
)

product_analysis = factory.groupby('product_name').agg(
    produced=('produced_units', 'sum'),
    defective=('defective_units', 'sum')
)

product_analysis['defect_rate'] = (
    product_analysis['defective'] / product_analysis['produced']
)

issue_summary = report_df.pivot_table(
    index='source_file',
    columns='issue_type',
    values='rows_count',
    aggfunc='sum',
    fill_value=0
)

issue_summary['total_issues'] = issue_summary.sum(axis=1)

suspicious_data.groupby('source_file').size()
duplicates.groupby('source_file').size()

duplicates[
    ['source_file', '_source_row', 'batch_id',
     'production_date', 'shift', 'product_name']
].sort_values('source_file')
print(duplicates)