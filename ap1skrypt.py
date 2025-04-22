import arcpy
import os

#%% Ustawienie środowiska
arcpy.env.workspace ="C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy"
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("ETRF2000-PL_CS92")
arcpy.env.extent ="C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy\A03_Granice_gmin_1992_Buffer.shp"
arcpy.env.mask = "C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy\A03_Granice_gmin_1992_Buffer.shp"
arcpy.env.cellSize = 5
arcpy.env.overwriteOutput = True
nmt = r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\NMT\NMTCaly.tif"



#%% Zmiana nazw plików tak by nie zawierały kropek
directory1 = arcpy.env.workspace
teryt1 ="0210"
teryt2="0212"


for filename in os.listdir(directory1):
    name, extension = os.path.splitext(filename)    
    if '.' in name:   
        new_name = name.replace('.', '')    
        new_filename = new_name + extension  
        old_file = os.path.join(directory1, filename) 
        new_file = os.path.join(directory1, new_filename) 
        if not os.path.exists(new_file):    
            os.rename(old_file, new_file)   
            
      
#znalezienie warstw potrzebnych w projekcie
for filename in os.listdir(directory1): #przeszukanie folderu z warstwami
    if teryt1+"__OT_PTWP" in filename and filename.endswith(".shp"):    #sprawdzenie czy nazwa pliku zawiera TERYT i OT_PTWP oraz kończy się na .shp
        ptwp_lubanski = filename    #przypisanie nazwy pliku do zmiennej
    elif teryt2+"__OT_PTWP" in filename and filename.endswith(".shp"): #analogicznie jak wyżej
        ptwp_lwowecki = filename
    elif teryt1+"__OT_SWRS" in filename and filename.endswith(".shp"): 
        swrs_lubanski = filename
    elif teryt2+"__OT_SWRS" in filename and filename.endswith(".shp"): 
        swrs_lwowecki = filename
    elif teryt1+"__OT_BUBD" in filename and filename.endswith(".shp"):
        bubd_lubanski = filename
    elif teryt2+"__OT_BUBD" in filename and filename.endswith(".shp"):
        bubd_lwowecki = filename
    elif teryt1+"__OT_PTLZ" in filename and filename.endswith(".shp"):
        ptlz_lubanski = filename
    elif teryt2+"__OT_PTLZ" in filename and filename.endswith(".shp"):
        ptlz_lwowecki = filename
    elif teryt1+"__OT_SKDR" in filename and filename.endswith(".shp"):
        skdr_lubanski = filename
    elif teryt2+"__OT_SKDR" in filename and filename.endswith(".shp"):
        skdr_lwowecki = filename
    elif teryt1+"__OT_SKJZ" in filename and filename.endswith(".shp"):
        skjz_lubanski = filename
    elif teryt2+"__OT_SKJZ" in filename and filename.endswith(".shp"):
        skjz_lwowecki = filename
    elif teryt1+"__OT_SKRW" in filename and filename.endswith(".shp"):
        skrw_lubanski = filename
    elif teryt2+"__OT_SKRW" in filename and filename.endswith(".shp"):
        skrw_lwowecki = filename
    elif teryt1+"__OT_SULN" in filename and filename.endswith(".shp"):
        suln_lubanski = filename
    elif teryt2+"__OT_SULN" in filename and filename.endswith(".shp"):
        suln_lwowecki = filename

      
# REALIZACJA KRYTERIUM 1 - ODLEGŁOŚĆ OD WÓD

# złączenie warstw z dwóch powiatów w jedną dla rzek i wód powierzchniowych
arcpy.management.Merge(
    inputs=[swrs_lubanski,swrs_lwowecki],
    output="swrs_merge"
)
arcpy.management.Merge(
    inputs=[ptwp_lwowecki,ptwp_lubanski],
    output="ptwp_merge"
)

# zmiana geometrii rzek z linii na poligony, by warstwa rzek i wód powierzchniowych miała tę samą geometrię
arcpy.analysis.Buffer(
    in_features="swrs_merge",
    out_feature_class="swrs_poly",
    buffer_distance_or_field="1 Centimeters",
)

# złączenie warstw rzek i wód powierzchniowych
arcpy.management.Merge(
    inputs=["swrs_poly","ptwp_merge"],
    output="wody"
)

#stworzenie mapy odległości od wód powierzchniowych
eucDist_wody = arcpy.sa.EucDistance(
    in_source_data="wody", 
    cell_size=5)
#eucDist_wody.save("eucDist_wody")

#stworzenie funkcji przydatności 
wody_frosnaca = arcpy.sa.FuzzyMembership(
    in_raster=eucDist_wody,
    fuzzy_function = "LINEAR 100 102"
)

wody_fmalejaca = arcpy.sa.FuzzyMembership(
    in_raster=eucDist_wody,
    fuzzy_function = "LINEAR 1000 200 "
)

#stworzenie mapy przydatności dla kryterium1 1 poprzez połączenie funkcji przydatności i jej zapis
mapa_przydatnosci_wody = arcpy.sa.FuzzyOverlay(
    in_rasters=[wody_frosnaca,wody_fmalejaca],
    overlay_type="AND")
mapa_przydatnosci_wody.save("kryterium1.tif")

#REALIZACJA KRYTERIUM 2 - ODLEGŁOŚĆ OD BUDYNKÓW MIESZKALNYCH

#złączenie warstw budynków z dwóch powiatów w jedną
arcpy.management.Merge(
    inputs=[bubd_lwowecki,bubd_lubanski],
    output="bubd_merge"
)

# wybranie budynków mieszkalnych
bubd_selection= arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="bubd_merge",
    where_clause="FOBUD LIKE 'budynki mieszkalne'"
)
arcpy.management.CopyFeatures(bubd_selection, 'bubd_mieszkalne')

# stworzenie mapy odległości od budynków mieszkalnych
eucDist_budynki = arcpy.sa.EucDistance(
    in_source_data="bubd_mieszkalne", 
    cell_size=5)

#stworzenie funkcji przydatności
# uzanano, że optymalnie będzie powyżej 1500 m od budynków mieszkalnych
budynki_frosnaca = arcpy.sa.FuzzyMembership(
    in_raster=eucDist_budynki,
    fuzzy_function="LINEAR 150 1000"
)
budynki_frosnaca.save("kryterium2.tif")



# REALIZACJA KRYTERIUM 3 - ODLEGŁOŚĆ OD LASÓW
#złączenie odpowiednich warstw z dwóch powiatów w jedną
arcpy.management.Merge(
    inputs=[ptlz_lwowecki,ptlz_lubanski],
    output="ptlz_merge"
)

#wyselekcjonowanie lasów
ptlz_selection = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="ptlz_merge",
    where_clause="RODZAJ = 'las'"
)
arcpy.management.CopyFeatures(ptlz_selection, 'ptlz_lasy')

# stworzenie mapy odległości od lasów
eucDist_lasy = arcpy.sa.EucDistance(
    in_source_data="ptlz_lasy", 
    cell_size=5)

# stworzenie funkcji przydatności
#poniżej 15 m od lasu funkcja ma wartość 0, od 15 do 100m funkcja rośnie, od 101 do 1000m funkcja ma wartość 1, w przedziale 1000-1500 funkcja maleje
lasy_frosnaca = arcpy.sa.FuzzyMembership(
    in_raster=eucDist_lasy,
    fuzzy_function="LINEAR 15 100"
)

lasy_fmalejaca = arcpy.sa.FuzzyMembership(
    in_raster=eucDist_lasy,
    fuzzy_function="LINEAR 1500 1000"
)

#połączenie funkcji przydatności
mapa_przydatnosci_lasy = arcpy.sa.FuzzyOverlay(
    in_rasters=[lasy_frosnaca,lasy_fmalejaca],
    overlay_type="AND")

mapa_przydatnosci_lasy.save("kryterium3.tif")


# REALIZACJA KRYTERIUM 4 - ZAGĘSZCZENIE DRÓG UTWARDZONYCH

#złączenie warstw dróg z dwóch powiatów w jedną
arcpy.management.Merge(
    inputs=[skdr_lwowecki,skdr_lubanski],
    output="skdr_merge"
)

#wybranie dróg utwardzonych
skdr_selection= arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="skdr_merge",
    where_clause = "MATE_NAWIE IN ('beton','bruk', 'kostka kamienna', 'kostka prefabrykowana', 'masa bitumiczna', 'płyty betonowe')"
)
arcpy.management.CopyFeatures(skdr_selection, 'skdr_utwardzone')

# obliczenie gęstości dróg
line_den_skdr = arcpy.sa.LineDensity(
    in_polyline_features="skdr_utwardzone",
    population_field="NONE",
    cell_size=5,
    search_radius=1000,
    area_unit_scale_factor="SQUARE_METERS"
)


# wybranie maksymalnej wartości by użyć jej do przeskalowania do wartości 0-1
lide_den_skdr_max = line_den_skdr.maximum

#przeskalowanie wartości do wartości 0-1
lide_den_skdr_rescale = arcpy.sa.RescaleByFunction(
    in_raster=line_den_skdr,
    transformation_function="LINEAR 0 lide_den_skrd_max 0 # lide_den_skrd_max #",
    from_scale=0,
    to_scale=1
)
lide_den_skdr_rescale.save("kryterium4.tif")


#REALIZACJA KRYTERIUM 5 - NACHYLENIE STOKÓW OPTYMALNIE

#stworzenie mapy spadków z wykorzystaniem narzędzia Slope
slope = arcpy.ddd.Slope(
    in_raster=nmt,
    out_raster='slope',
    output_measurement="PERCENT_RISE",
    z_factor=1
)

#stworzenie funkcji przydatności 
#uznano, że optymalne nachylenie stoków to 0-3%, powyżej 10% stoki nie są przydatne
slope_fmalejaca = arcpy.sa.FuzzyMembership(
    in_raster=slope,
    fuzzy_function="LINEAR 10 3"
)
slope_fmalejaca.save("kryterium5.tif")

#REALIZACJA KRYTERIUM 6 - EKSPONACJA SŁONECZNA

# stworzenie mapy wystawy słonecznej z wykorzystaniem narzędzia Aspect
aspect=arcpy.ddd.Aspect(
    in_raster=nmt,
    out_raster="aspect"
)

#stworzenie funkcji przydatności
#dla stoków południowo-zachodnich i południowo-wschodnich funkcja przydatności rośnie liniowo, dla stoków południowych ma wartość 1
apect_frosnaca = arcpy.sa.FuzzyMembership(
    in_raster=aspect,
    fuzzy_function="LINEAR 113 158"
)

aspect_fmalejaca = arcpy.sa.FuzzyMembership(
    in_raster=aspect,
    fuzzy_function="LINEAR 248 203"
)
                    
#połączenie funkcji przydatności i stworzenie mapy przydatności
mapa_przydatnosci_aspect = arcpy.sa.FuzzyOverlay(
    in_rasters=[aspect_fmalejaca,apect_frosnaca],
    overlay_type="AND")
mapa_przydatnosci_aspect.save("kryterium6.tif")





#REALIZACJA KRYTERIUM 7: DOBRY DOJAZD OD ISTOTNYCH DROGOWYCH WĘZŁÓW KOMUNIKACYJNYCH
#czytanie warstwy wygenerowanej z użyciem narzędzia ......... w QGIS
# #Węzły komunikacyjne pobrano z bdotu, w 0210 nie był w 0212 były 3. 
# Jako drogi dla pojazdów ciężkich wybrano drogi utwardzone.
# w QGIS skorzystano z narzędzia Iso - Area as Interpolation (from Layer) dostarczanego z wtyczką QNEAT3

interpolacja = r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy\interpolacja.tif"
interpolacja_max = float ( arcpy.management.GetRasterProperties(interpolacja,"MAXIMUM") [0].replace (',','.'))

# Ustawienie wartości NoData na 30000
interpolacja_data = arcpy.sa.Con(
    in_conditional_raster=interpolacja,
    in_true_raster_or_constant=30000,
    in_false_raster_or_constant=interpolacja,
    where_clause="VALUE IS NULL"
)
 
#stworzenie funkcji przydatności 
#uznano, że ...........
wezly_fmalejaca = arcpy.sa.FuzzyMembership(
    in_raster=interpolacja_data,
    fuzzy_function = f"LINEAR {0.7*interpolacja_max} {0.45*interpolacja_max} ")

wezly_fmalejaca.save("kryterium7.tif")


#Stworzenie kryteriów ostrych
#woda
wody_max = eucDist_wody.maximum
wody_ostre = arcpy.sa.Reclassify(
    in_raster=eucDist_wody,
    reclass_field="VALUE",
    remap=f"0 100 0;100 {wody_max} 1",
    missing_values="NODATA"
)
wody_ostre.save("kryterium_ostre1.tif")

#budynki
budynki_max = eucDist_budynki.maximum
budynki_ostre = arcpy.sa.Reclassify(
    in_raster=eucDist_budynki,
    reclass_field="VALUE",
    remap=f"0 150 0;150 {budynki_max} 1",
    missing_values="NODATA"
)
budynki_ostre.save("kryterium_ostre2.tif")

#lasy
lasy_max = eucDist_lasy.maximum
lasy_ostre = arcpy.sa.Reclassify(
    in_raster=eucDist_lasy,
    reclass_field="VALUE",
    remap=f"0 15 0;15 {lasy_max} 1",
    missing_values="NODATA"    
)
lasy_ostre.save("kryterium_ostre3.tif")

#stoki
slope_max = arcpy.GetRasterProperties_management(slope, "MAXIMUM").getOutput(0)
stoki_ostre = arcpy.sa.Reclassify(
    in_raster=slope,
    reclass_field="VALUE",
    remap=f"0 10 1;10 {slope_max} 0",
)
stoki_ostre.save("kryterium_ostre4.tif")

    

#połączenie kryteriów rozmytych
#podejście z równymi wagami
waga = 1/7
table_rowne = arcpy.sa.WSTable([["kryterium1.tif", "VALUE", waga],
                        ["kryterium2.tif", "VALUE", waga],
                        ["kryterium3.tif", "VALUE", waga],
                        ["kryterium4.tif", "VALUE", waga],
                        ["kryterium5.tif", "VALUE", waga],
                        ["kryterium6.tif", "VALUE", waga],
                        ["kryterium7.tif", "VALUE", waga]])

kryteria_rowne= arcpy.sa.WeightedSum(table_rowne)
kryteria_rowne.save("kryteria_rowne.tif")



#połączenie kryteriów ostrych
kryteria_ostre = arcpy.sa.FuzzyOverlay(
    in_rasters=["kryterium_ostre1.tif","kryterium_ostre2.tif","kryterium_ostre3.tif","kryterium_ostre4.tif"],
    overlay_type="AND"
)
kryteria_ostre.save("kryteria_ostre.tif")

#połączenie kryteriów rozmytych i ostrych w podejściu z równymi wagami
kryteria_polaczone = arcpy.sa.FuzzyOverlay(
    in_rasters=[kryteria_ostre,kryteria_rowne],
    overlay_type="AND"
    )
kryteria_polaczone.save("kryteria_polaczone_rowne.tif")

kryteria_polaczone = arcpy.sa.FuzzyOverlay(
    in_rasters=[kryteria_ostre,kryteria_rozne],
    overlay_type="AND"
    )

#reklasyfikacja uzyskanej mapy przydatności
kryteria_polaczone_max = kryteria_polaczone.maximum
granica_przydatnosci = 0.5*kryteria_polaczone_max   #!!!!!!!!!!!Zmiana z 80% na 50%

kryteria_polaczone_reclass = arcpy.sa.Reclassify(
    in_raster="kryteria_polaczone_rowne.tif",
    reclass_field="VALUE",
    remap=f"0 {granica_przydatnosci}  0; {granica_przydatnosci} 1 1",
    missing_values="NODATA"
)
kryteria_polaczone_reclass.save("kryteria_polaczone_reclass1.tif")

#podejście z różnymi wagami

#zmiana rastra na shapefile
arcpy.conversion.RasterToPolygon(
    in_raster="kryteria_polaczone_reclass1.tif",
    out_polygon_features="kryteria_polaczone_shp1",
    simplify="SIMPLIFY",
    raster_field="Value",
    create_multipart_features="SINGLE_OUTER_PART",
    max_vertices_per_feature=None
)
# wybranie poligonów które mają 'gridcode' = 1
obszary_przydatne_rowne = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="kryteria_polaczone_shp1",
    where_clause = "gridcode = 1"
)
arcpy.management.CopyFeatures(obszary_przydatne_rowne, 'obszary_przydatne_rowne')



#złączenie warstw działek z dwóch powiatów w jedną
arcpy.management.Merge(
    inputs=["dzialki0210","dzialki0212"],
    output="dzialki_merge"
)


#wybranie działek, które leża na przydatnych obszarach
arcpy.analysis.SummarizeWithin(
    in_polygons="dzialki_merge",
    in_sum_features="obszary_przydatne_rowne",
    out_feature_class=r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\MyProject\MyProject.gdb\dzialki_przydatne_rowne_wagi",
    keep_all_polygons="ONLY_INTERSECTING",
    sum_fields=None,
    sum_shape="ADD_SHAPE_SUM",
    shape_unit="HECTARES",
    group_field=None,
    add_min_maj="NO_MIN_MAJ",
    add_group_percent="NO_PERCENT",
    out_group_table=None
)

# wyeksportowanie wyniku narzędzia SummarizeWithin do pliku shp do folderu ze wszytskimi warstwami
#arcgis wymaga by wynik narzędzia SummarizeWithin był w w geobazie lub in_memory
arcpy.conversion.FeatureClassToShapefile(
    [r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\MyProject\MyProject.gdb\dzialki_przydatne_rowne_wagi"],  
    r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy"  # Folder docelowy
)

#obliczenie ile procent powierzchni działek jest na obszarach przydatnych
dzialki_przydatne_rowne_wagi = r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy\dzialki_przydatne_rowne_wagi.shp"
arcpy.management.CalculateField(
    in_table="dzialki_przydatne_rowne_wagi",
    field="pow_przyd",
    expression="100*!sum_Area_H!/(!Shape_Area! / 10000)",
    expression_type="PYTHON3",
    code_block="",
    field_type="FLOAT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

#wybranie tych działek, których min. 60% powierzchni stanowią obszary przydatne i zapisanie ich do nowej warstwy
dzialki_przydatne_rowne_wagi_60 = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view=dzialki_przydatne_rowne_wagi,
    selection_type="NEW_SELECTION",
    where_clause="pow_przyd >= 60"
)
arcpy.management.CopyFeatures(dzialki_przydatne_rowne_wagi_60, 'dzialki_przydatne_rowne_wagi_60')

#połączenie sąsiadujących działek w jeden obiekt 
arcpy.management.Dissolve(
    in_features="dzialki_przydatne_rowne_wagi_60",
    out_feature_class="dzialki_rowne_wagi_dissolve",
    dissolve_field=None,
    statistics_fields=None,
    multi_part="SINGLE_PART",
    unsplit_lines="DISSOLVE_LINES",
    concatenation_separator=""
)

#obliczenie powierzchni (w m2) i obwodu (w m) działek po połączeniu 
arcpy.management.CalculateGeometryAttributes(
    in_features="dzialki_rowne_wagi_dissolve",
    geometry_property="area AREA;obw PERIMETER_LENGTH",
    length_unit="METERS",
    area_unit="SQUARE_METERS",
    coordinate_system='PROJCS["ETRF2000-PL_CS92",GEOGCS["ETRF2000-PL",DATUM["ETRF2000_Poland",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",-5300000.0],PARAMETER["Central_Meridian",19.0],PARAMETER["Scale_Factor",0.9993],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]',
    coordinate_format="SAME_AS_INPUT"
)
    
#wybranie działek/grup działek które mają powierzchnię minimum 2ha i zapisanie ich do nowej warstwy
dzialki_rowne_wagi_2ha = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="dzialki_rowne_wagi_dissolve",
    selection_type="NEW_SELECTION",
    where_clause="area >= 20000"
)
arcpy.management.CopyFeatures(dzialki_rowne_wagi_2ha, 'dzialki_rowne_wagi_2ha')

#stworzenie otoczki wypukłej dla działek by otrzymać atrubuty geometrii dla grup działek
arcpy.management.MinimumBoundingGeometry(
    in_features="dzialki_rowne_wagi_2ha",
    out_feature_class="dzialki_rowne_wagi_otoczka",
    geometry_type="RECTANGLE_BY_WIDTH",
    group_option="NONE",
    group_field=None,
    mbg_fields_option="MBG_FIELDS"
)
arcpy.management.JoinField(
    in_data="dzialki_rowne_wagi_2ha",
    in_field="FID",
    join_table="dzialki_rowne_wagi_otoczka",
    join_field="FID",
    fields="MBG_Width",
    fm_option="NOT_USE_FM",
    field_mapping=None,
    index_join_fields="NO_INDEXES"
)
#wybranie grup działek, które mają szerokośc min. 50 metrów i zapisanie ich do nowej warstwy
dzialki_rowne_wagi_szerokosc50 = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="dzialki_rowne_wagi_2ha",
    selection_type="NEW_SELECTION",
    where_clause="MBG_Width >= 50"
)
arcpy.management.CopyFeatures(dzialki_rowne_wagi_szerokosc50, 'dzialki_rowne_wagi_szerokosc50')

#***********************************************************************************************************************************************************************
kryteria_ostre = arcpy.sa.FuzzyOverlay(
    in_rasters=["kryterium_ostre1.tif","kryterium_ostre2.tif","kryterium_ostre3.tif","kryterium_ostre4.tif"],
    overlay_type="AND"
)
#podejście z różnymi wagami
#połączenie kryteriów rozmytych
table_rozne = arcpy.sa.WSTable([["kryterium1.tif", "VALUE", 0.05],
                        ["kryterium2.tif", "VALUE", 0.1],
                        ["kryterium3.tif", "VALUE", 0.05],
                        ["kryterium4.tif", "VALUE", 0.15],
                        ["kryterium5.tif", "VALUE", 0.25],
                        ["kryterium6.tif", "VALUE", 0.25],
                        ["kryterium7.tif", "VALUE", 0.15]])

kryteria_rozne= arcpy.sa.WeightedSum(table_rozne)
kryteria_rozne.save("kryteria_rozne.tif")

#połączenie kryteriów rozmytych i ostrych w podejściu z różnymi wagami
kryteria_polaczone = arcpy.sa.FuzzyOverlay(
    in_rasters=[kryteria_ostre,kryteria_rozne],
    overlay_type="AND"
    )
kryteria_polaczone.save("kryteria_polaczone_rozne.tif")


#reklasyfikacja uzyskanej mapy przydatności
kryteria_polaczone_max = kryteria_polaczone.maximum
granica_przydatnosci = 0.5*kryteria_polaczone_max   

kryteria_polaczone_reclass = arcpy.sa.Reclassify(
    in_raster="kryteria_polaczone_rozne.tif",
    reclass_field="VALUE",
    remap=f"0 {granica_przydatnosci}  0; {granica_przydatnosci} 1 1",
    missing_values="NODATA"
)
kryteria_polaczone_reclass.save("kryteria_polaczone_reclass2.tif")

#zmiana rastra na shapefile
arcpy.conversion.RasterToPolygon(
    in_raster="kryteria_polaczone_reclass2.tif",
    out_polygon_features="kryteria_polaczone_shp2",
    simplify="SIMPLIFY",
    raster_field="Value",
    create_multipart_features="SINGLE_OUTER_PART",
    max_vertices_per_feature=None
)
# wybranie poligonów które mają 'gridcode' = 1
obszary_przydatne_rozne = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="kryteria_polaczone_shp2",
    where_clause = "gridcode = 1"
)
arcpy.management.CopyFeatures(obszary_przydatne_rozne, 'obszary_przydatne_rozne')


#wybranie działek, które leża na przydatnych obszarach
# try:
#     arcpy.analysis.SummarizeWithin(
#         in_polygons="dzialki_merge",
#         in_sum_features="obszary_przydatne_rozne",
#         out_feature_class=r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\MyProject\MyProject.gdb\dzialki_przydatne_rozne_wagi",
#         keep_all_polygons="ONLY_INTERSECTING",
#         sum_fields=None,
#         sum_shape="ADD_SHAPE_SUM",
#         shape_unit="HECTARES",
#         group_field=None,
#         add_min_maj="NO_MIN_MAJ",
#         add_group_percent="NO_PERCENT",
#         out_group_table=None
#     )
#     print("SummarizeWithin executed successfully.")
# except arcpy.ExecuteError:
#     print(f"ArcPy Error: {arcpy.GetMessages(2)}")
# except Exception as e:
#     print(f"Python Error: {str(e)}")

# wyeksportowanie wyniku narzędzia SummarizeWithin do pliku shp do folderu ze wszytskimi warstwami
#arcgis wymaga by wynik narzędzia SummarizeWithin był w w geobazie lub in_memory
# arcpy.conversion.FeatureClassToShapefile(
#     [r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\MyProject\MyProject.gdb\dzialki_przydatne_rozne_wagi"],  
#     r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy"  # Folder docelowy
# )

#obliczenie ile procent powierzchni działek jest na obszarach przydatnych
dzialki_przydatne_rozne_wagi = r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\warstwy\dzialki_przydatne_rozne_wagi.shp"


arcpy.management.CalculateField(
    in_table=dzialki_przydatne_rozne_wagi,
    field="pow_przyd",
    expression="100*!sum_Area_H!/(!Shape_Area! / 10000)",
    expression_type="PYTHON3",
    code_block="",
    field_type="FLOAT",
    enforce_domains="NO_ENFORCE_DOMAINS"
)

#wybranie tych działek, których min. 60% powierzchni stanowią obszary przydatne i zapisanie ich do nowej warstwy
dzialki_przydatne_rozne_wagi_60 = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view=dzialki_przydatne_rozne_wagi,
    selection_type="NEW_SELECTION",
    where_clause="pow_przyd >= 60"
)
arcpy.management.CopyFeatures(dzialki_przydatne_rozne_wagi_60, 'dzialki_przydatne_rozne_wagi_60')

#połączenie sąsiadujących działek w jeden obiekt 
arcpy.management.Dissolve(
    in_features="dzialki_przydatne_rozne_wagi_60",
    out_feature_class="dzialki_rozne_wagi_dissolve",
    dissolve_field=None,
    statistics_fields=None,
    multi_part="SINGLE_PART",
    unsplit_lines="DISSOLVE_LINES",
    concatenation_separator=""
)

#obliczenie powierzchni (w m2) i obwodu (w m) działek po połączeniu 
arcpy.management.CalculateGeometryAttributes(
    in_features="dzialki_rozne_wagi_dissolve",
    geometry_property="area AREA;obw PERIMETER_LENGTH",
    length_unit="METERS",
    area_unit="SQUARE_METERS",
    coordinate_system='PROJCS["ETRF2000-PL_CS92",GEOGCS["ETRF2000-PL",DATUM["ETRF2000_Poland",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",-5300000.0],PARAMETER["Central_Meridian",19.0],PARAMETER["Scale_Factor",0.9993],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]',
    coordinate_format="SAME_AS_INPUT"
)
    
#wybranie działek/grup działek które mają powierzchnię minimum 2ha i zapisanie ich do nowej warstwy
dzialki_rozne_wagi_2ha = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="dzialki_rozne_wagi_dissolve",
    selection_type="NEW_SELECTION",
    where_clause="area >= 20000"
)
arcpy.management.CopyFeatures(dzialki_rozne_wagi_2ha, 'dzialki_rozne_wagi_2ha')

#stworzenie otoczki wypukłej dla działek by otrzymać atrubuty geometrii dla grup działek
arcpy.management.MinimumBoundingGeometry(
    in_features="dzialki_rozne_wagi_2ha",
    out_feature_class="dzialki_rozne_wagi_otoczka",
    geometry_type="RECTANGLE_BY_WIDTH",
    group_option="NONE",
    group_field=None,
    mbg_fields_option="MBG_FIELDS"
)
arcpy.management.JoinField(
    in_data="dzialki_rozne_wagi_2ha",
    in_field="FID",
    join_table="dzialki_rozne_wagi_otoczka",
    join_field="FID",
    fields="MBG_Width",
    fm_option="NOT_USE_FM",
    field_mapping=None,
    index_join_fields="NO_INDEXES"
)
#wybranie grup działek, które mają szerokośc min. 50 metrów i zapisanie ich do nowej warstwy
dzialki_rozne_wagi_szerokosc50 = arcpy.management.SelectLayerByAttribute(
    in_layer_or_view="dzialki_rozne_wagi_2ha",
    selection_type="NEW_SELECTION",
    where_clause="MBG_Width >= 50"
)
arcpy.management.CopyFeatures(dzialki_rozne_wagi_szerokosc50, 'dzialki_rozne_wagi_szerokosc50')


#Stworzenie funkcji klasyfikującej i przypisanie poszczególnym typom pokrycia terenu kosztów jednostkowych
codeblock = """
def liczkoszt(kod):
    if kod == "PTWP01":
        return 0
    elif kod == "PTWP02":
        return 200
    elif kod == "PTWP03":
        return 0
    elif kod == "PTZB02":
        return 100
    elif kod == "PTZB01":
        return 200
    elif kod == "PTZB03":
        return 200
    elif kod == "PTZB04":
        return 200
    elif kod == "PTZB05":
        return 50
    elif kod == "PTLZ01":
        return 100
    elif kod == "PTLZ02":
        return 50
    elif kod == "PTLZ03":
        return 50
    elif kod == "PTRK01":
        return 15
    elif kod == "PTRK02":
        return 15
    elif kod == "PTUT03":
        return 100
    elif kod == "PTUT02":
        return 90
    elif kod == "PTUT04":
        return 20
    elif kod == "PTUT05":
        return 20
    elif kod == "PTUT01":
        return 0
    elif kod == "PTTR02":
        return 1
    elif kod == "PTTR01":
        return 20
    elif kod == "PTKM01":
        return 100
    elif kod == "PTKM02":
        return 200
    elif kod == "PTKM03":
        return 170
    elif kod == "PTKM04":
        return 200
    elif kod == "PTGN01":
        return 1
    elif kod == "PTGN02":
        return 1
    elif kod == "PTGN03":
        return 1
    elif kod == "PTGN04":
        return 1
    elif kod == "PTPL01":
        return 50
    elif kod == "PTSO01":
        return 0
    elif kod == "PTSO02":
        return 0
    elif kod == "PTWZ01":
        return 0
    elif kod == "PTWZ02":
        return 0
    elif kod == "PTNZ01":
        return 150
    elif kod == "PTNZ02":
        return 150
    else:
        return 0

 """   
PT = r"C:\studia\sem5\AnalizyPrzestrzenne\Proj1\mapa_kosztow_BDOT10k_dane_archiwalne\PT_merge_cliped.shp"
arcpy.management.AddField(PT, "koszt", "DOUBLE", None, None, None, '',"NULLABLE", "REQUIRED")


PT_koszty = arcpy.management.CalculateField(
    in_table=PT,
    field="koszt",
    expression="liczkoszt(!X_KOD!)",
    expression_type="PYTHON3",
    code_block=codeblock,

)

#zmiana warstwy wektorowej na rastrową
koszty_raster=arcpy.conversion.FeatureToRaster(
    in_features=PT_koszty,
    field="koszt",
    out_raster="koszty_raster",
    cell_size=5
)

#Przypisanie pikselom obszarów bariery absolutnej wartości braku danych dla obszarów bariery absolutnej
mapa_kosztow_wzglednych = arcpy.sa.SetNull(
        in_conditional_raster=koszty_raster,
        in_false_raster_or_constant=koszty_raster,
        where_clause="VALUE = 0"
    )
mapa_kosztow_wzglednych.save("mapa_kosztow_wzglednych.tif")


#podejście z równymi wagami
#stworzenie mapy kosztów skumulowanych i mapy kierunków
cost_map_rowne_wagi = arcpy.sa.CostDistance(
    in_source_data="dzialki_rowne_wagi_szerokosc50",
    in_cost_raster="mapa_kosztow_wzglednych.tif",
    maximum_distance=None,
    out_backlink_raster="backlink_rowne_wagi.tif",
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
cost_map_rowne_wagi.save("cost_map_rowne_wagi.tif")

#stworzenie ścieżki przyłącza

    #złączenie odpowiednich warstw z dwóch powiatów w jedną
arcpy.management.Merge(
inputs=[suln_lubanski,suln_lwowecki],
output="suln_merge"
)

cost_path_rowne_wagi = arcpy.sa.CostPath(
    in_destination_data="suln_merge",
    in_cost_distance_raster="cost_map_rowne_wagi.tif",
    in_cost_backlink_raster="backlink_rowne_wagi.tif",
    path_type="BEST_SINGLE",
    force_flow_direction_convention="INPUT_RANGE"
)
cost_path_rowne_wagi.save("cost_path_rowne_wagi.tif")

#stworzenie ścieżki przyłącza w postaci wektorowej
arcpy.conversion.RasterToPolyline(
    in_raster=cost_path_rowne_wagi,
    out_polyline_features="cost_path_rowne_wagi_vector",
)


#podejście z różnymi wagami
#stworzenie mapy kosztów skumulowanych i mapy kierunków
cost_map_rozne_wagi = arcpy.sa.CostDistance(
    in_source_data="dzialki_rozne_wagi_szerokosc50",
    in_cost_raster="mapa_kosztow_wzglednych.tif",
    maximum_distance=None,
    out_backlink_raster="backlink_rozne_wagi.tif",
    source_cost_multiplier=None,
    source_start_cost=None,
    source_resistance_rate=None,
    source_capacity=None,
    source_direction=""
)
cost_map_rozne_wagi.save("cost_map_rozne_wagi.tif")

#stworzenie ścieżki przyłącza
cost_path_rozne_wagi = arcpy.sa.CostPath(
    in_destination_data="suln_merge",
    in_cost_distance_raster="cost_map_rozne_wagi.tif",
    in_cost_backlink_raster="backlink_rozne_wagi.tif",
    path_type="BEST_SINGLE",
    force_flow_direction_convention="INPUT_RANGE"
)
cost_path_rozne_wagi.save("cost_path_rozne_wagi.tif")

#stworzenie ścieżki przyłącza w postaci wektorowej
arcpy.conversion.RasterToPolyline(
    in_raster=cost_path_rozne_wagi,
    out_polyline_features="cost_path_rozne_wagi_vector",
)


