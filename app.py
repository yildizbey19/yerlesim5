import pandas as pd
import numpy as np
import streamlit as st
import itertools

def input_data(excel_file):
    variables = []
    types = []
    components = []

    df = pd.read_excel(excel_file, sheet_name='Sayfa1')

    variable_column = 'Değişkenler'
    type_column = 'Konum tipleri'
    component_column = 'İlişkili konumlar'

    if variable_column in df.columns:
        variables = df[variable_column].dropna().tolist()
    else:
        raise ValueError(f"{variable_column} sütunu bulunamadı.")

    if type_column in df.columns:
        types = df[type_column].dropna().tolist()
    else:
        raise ValueError(f"{type_column} sütunu bulunamadı.")

    if component_column in df.columns:
        components = df[component_column].dropna().tolist()
    else:
        raise ValueError(f"{component_column} sütunu bulunamadı.")

    return variables, types, components

def calculate_total_cost(mapping, df, distance_df):
    total_cost = 0
    varcomp = list(mapping.keys())
    for var1 in varcomp:
        for var2 in varcomp:
            if var1 != var2:
                cost = get_user_input(var1, var2, df, distance_df)
                distance = get_distance(mapping[var1], mapping[var2], distance_df)
                total_cost += cost * distance
    return total_cost

def get_user_input(cıkıs, varıs, df, distance_df):
    filtered_df = df[(df['nerden'] == cıkıs) & (df['nereye'] == varıs)]
    total_cost = 0
    malzeme_kodları = []
    for _, row in filtered_df.iterrows():
        F = float(str(row['sıklık']).replace(',', '.'))
        OHM = float(str(row['birim maliyet']).replace(',', '.'))
        distance = get_distance(cıkıs, varıs, distance_df)
        cost = F * OHM * distance
        total_cost += cost
        malzeme_kodları.append(row['malzeme kodu'])  # Malzeme kodlarını toplama
    return total_cost, malzeme_kodları  # İki değer döndürme


def get_distance(cıkıs, varıs, distance_df):
    try:
        if cıkıs in distance_df.index and varıs in distance_df.columns:
            distance = distance_df.loc[cıkıs, varıs]
            return 1 if pd.isna(distance) else distance
        else:
            return 1
    except KeyError:
        return 1


def main():
    st.title("Taşıma Maliyeti Hesabına Göre Değişkenlere Yerleşim Yeri Ata")
    
    uploaded_file = st.file_uploader("Excel dosyanızı yükleyin", type="xlsx")
    
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, sheet_name='Sayfa1')
        variables, types, components = input_data(uploaded_file)
        
        distance_df = pd.read_excel(uploaded_file, sheet_name='Sayfa1', usecols=f'N:{chr(78 + len(types+components))}', nrows=len(types+components), index_col=0)

        all_combinations = list(itertools.permutations(types, len(variables)))
        
        min_cost = float('inf')
        best_combination = None
        all_results = []

        for combination in all_combinations:
            mapping = dict(zip(variables, combination))
            mapping.update({component: component for component in components})
            total_cost = calculate_total_cost(mapping, df, distance_df)
            all_results.append((combination, total_cost))
            if total_cost < min_cost:
                min_cost = total_cost
                best_combination = mapping
        
        if best_combination:
            result_df = pd.DataFrame(list(best_combination.items()), columns=["Değişkenler", "Yerleşeceği Yerler"])
            result_df = result_df[result_df["Değişkenler"].isin(variables)]

            # Satır numaralarını 1'den başlatma
            result_df.index = np.arange(1, len(result_df) + 1)

            # Tabloyu stilize et
            styled_df = result_df.style.set_table_styles(
                [{'selector': 'th', 'props': [('background-color', '#2B2B2B'), ('color', 'white'), ('font-weight', 'bold')]}]
            ).applymap(lambda _: 'background-color: #00CED1; color: #000000')

            st.table(styled_df.set_properties(**{'text-align': 'center'}))

            st.write(f"Toplam maliyet: {min_cost}")

            # Kullanıcıya diğer tüm kombinasyonları görme seçeneği sun
            if st.checkbox("Olası tüm kombinasyonların maliyetlerini göster"):
                all_results_df = pd.DataFrame(
                    [(dict(zip(variables, combo)), cost) for combo, cost in all_results],
                    columns=["Kombinasyon", "Maliyet"]
                )
                all_results_df.index = np.arange(1, len(all_results_df) + 1)
                
                # Stilize edilmiş tabloyu göster
                styled_all_results_df = all_results_df.style.set_table_styles(
                    [{'selector': 'th', 'props': [('background-color', '#2B2B2B'), ('color', 'white'), ('font-weight', 'bold')]}]
                ).applymap(lambda _: 'background-color: #FFFFFF; color: #000000')
                
                st.table(styled_all_results_df.set_properties(**{'text-align': 'center'}))
            
            # Malzeme koduna göre maliyet gösterimi
            selected_material = st.selectbox("Bir malzeme kodu seçin", df['malzeme kodu'].unique())
            if selected_material:
                selected_material_df = df[df['malzeme kodu'] == selected_material]
                total_cost, _ = get_user_input(
                    selected_material_df['nerden'].values[0], 
                    selected_material_df['nereye'].values[0], 
                    df, distance_df
                )
                st.write(f"Seçilen malzeme ({selected_material}) için toplam taşıma maliyeti: {total_cost}")

            # Nereden Nereye Seçimi ve Malzeme Gösterimi
            start_location = st.selectbox("Nereden", df['nerden'].unique())
            end_location = st.selectbox("Nereye", df['nereye'].unique())
            
            if start_location and end_location:
                total_cost = get_user_input(start_location, end_location, df, distance_df)
                st.write(f"Nereden: {start_location}, Nereye: {end_location} için toplam maliyet: {total_cost}")
                
        else:
            st.write("Geçerli bir kombinasyon bulunamadı.")

if __name__ == "__main__":
    main()
