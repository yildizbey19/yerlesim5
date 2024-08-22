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
                cost, _ = get_user_input(var1, var2, df, distance_df)
                distance = get_distance(mapping[var1], mapping[var2], distance_df)
                total_cost += cost * distance
    return total_cost

def get_user_input(cıkıs, varıs, df, distance_df):
    filtered_df = df[(df['Nereden'] == cıkıs) & (df['Nereye'] == varıs)]
    total_cost = 0
    malzeme_kodları = []
    for _, row in filtered_df.iterrows():
        F = float(str(row['Sıklık']).replace(',', '.'))
        OHM = float(str(row['Birim Maliyet']).replace(',', '.'))
        distance = get_distance(cıkıs, varıs, distance_df)
        cost = F * OHM * distance
        total_cost += cost
        malzeme_kodları.append(row['Malzeme Kodu'])
    return total_cost, malzeme_kodları

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
    
    # Şablon Excel dosyasını indirme bağlantısını ekleyin
    with open("YerleşimŞablon.xlsx", "rb") as file:
        st.download_button(
            label="Şablon Excel dosyasını indirmek için tıklayın",
            data=file,
            file_name="YerleşimŞablon.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
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
          
            st.header("Optimum Yerleşim Düzeni")

            result_df = pd.DataFrame(list(best_combination.items()), columns=["Değişkenler", "Yerleşeceği Yerler"])
            result_df = result_df[result_df["Değişkenler"].isin(variables)]

            # Satır numaralarını 1'den başlatma
            result_df.index = np.arange(1, len(result_df) + 1)

            # Tabloyu stilize et
            styled_df = result_df.style.set_table_styles(
                [{'selector': 'th', 'props': [('background-color', '#87CEFA'), ('color', 'white'), ('font-weight', 'bold')]}]
            ).applymap(lambda _: 'background-color: #00CED1; color: #000000')

            st.table(styled_df.set_properties(**{'text-align': 'center'}))

            st.write(f"Toplam maliyet: {min_cost}")

            # Kullanıcıya diğer tüm kombinasyonları görme seçeneği sun
            st.header(" Diğer Kombinasyonların Taşıma Maliyetleri")


            if st.checkbox("Bütün kombinasyonların maliyetlerini görmek için tıklayınız"):
                all_results_df = pd.DataFrame(
                    [(dict(zip(variables, combo)), cost) for combo, cost in all_results],
                    columns=["Kombinasyon", "Maliyet"]
                )
                all_results_df.index = np.arange(1, len(all_results_df) + 1)
                
                # Stilize edilmiş tabloyu göster
                styled_all_results_df = all_results_df.style.set_table_styles(
                    [{'selector': 'th', 'props': [('background-color', '#87cefa'), ('color', 'white'), ('font-weight', 'bold')]}]
                ).applymap(lambda _: 'background-color: #FFFFFF; color: #000000')
                
                st.table(styled_all_results_df.set_properties(**{'text-align': 'center'}))
            
            # Malzeme koduna göre maliyet gösterimi
            st.header("Optimum Düzen İçin Malzeme Koduna Göre Taşıma Maliyeti")

            selected_material = st.selectbox("Bir malzeme kodu seçin", df['Malzeme Kodu'].unique())
            if selected_material:
                selected_material_df = df[df['Malzeme Kodu'] == selected_material]
                cıkıs = selected_material_df['Nereden'].values[0]
                varıs = selected_material_df['Nereye'].values[0]# En iyi kombinasyona göre yerleşim yerleri bulun
                best_cıkıs = best_combination.get(cıkıs, cıkıs)
                best_varıs = best_combination.get(varıs, varıs)
                
                # Seçilen malzeme için toplam maliyeti hesapla
                total_cost, _ = get_user_input(cıkıs, varıs, selected_material_df, distance_df)
                
                # En iyi kombinasyona göre yeniden hesapla
                best_distance = get_distance(best_cıkıs, best_varıs, distance_df)
                adjusted_cost = total_cost * best_distance
                st.write(f"Seçilen ({selected_material}) kodlu malzeme  için toplam taşıma maliyeti: {adjusted_cost}")

            # Nereden Nereye Seçimi ve Malzeme Gösterimi
            st.header("Optimum Düzen İçin Bölümden Bölüme Toplam Taşıma Maliyeti")

            start_location = st.selectbox("Nereden", df['Nereden'].unique())
            end_location = st.selectbox("Nereye", df['Nereye'].unique())
            
            if start_location and end_location:
                # En iyi kombinasyona göre yerleşim yeri bulun
                best_start_location = best_combination.get(start_location, start_location)
                best_end_location = best_combination.get(end_location, end_location)
                # Seçilen lokasyonlar için toplam maliyeti hesapla
                total_cost, malzeme_kodları = get_user_input(start_location, end_location, df, distance_df)
                
                # En iyi kombinasyona göre yeniden hesapla
                best_distance = get_distance(best_start_location, best_end_location, distance_df)
                adjusted_cost = total_cost * best_distance
                
                st.write(f"{start_location} bölümünden ({best_start_location}'da yer alıyor), {end_location} bölümüne ({best_end_location}'da yer alıyor) taşınan malzeme kodları: {malzeme_kodları}")
                st.write(f"Optimum yerleşim düzeni için {start_location} bölümünden {end_location} bölümüne taşınan malzemelerin toplam taşıma maliyeti: {adjusted_cost}")
                

if __name__ == "__main__":
    main()
