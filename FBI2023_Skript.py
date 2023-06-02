import ifcopenshell
import ifcopenshell.util
from ifcopenshell.util.selector import Selector

import ifcpatch

import datetime
from dbfread import DBF
from collections import OrderedDict



model = ifcopenshell.open(r"C:\Users\user\Desktop\DA_Daten\FBI_Paper\Final\Modell_Bruecke_FBI2023.ifc")
selector = Selector()

#Schritt 3: Entfernen ungewollter Informationen
print("Schritt 3: Entfernen ungewollter Informationen")
for x in model.by_type("IfcElement"):
    ifcopenshell.api.run("material.unassign_material", model, product=x)
    print("Von " + str(x.Name) + " wurde das Material entfernt.")

for x in model.by_type("IfcElementType"):
    if x.HasAssociations != ():
        ifcopenshell.api.run("material.unassign_material", model, product=x)
        print("Von " + x.Name + " wurde das Material entfernt.")
    

for x in model.by_type("IfcMaterialConstituentSet"):
    print("Folgendes IfcMaterialConstituentSet wurde entfernt: " + str(x.Name))
    ifcopenshell.api.run("material.remove_constituent", model, constituent=x)
    
for x in model.by_type("IfcMaterial"):
    print("Folgendes IfcMaterial wurde entfernt: " + str(x.Name))
    ifcopenshell.api.run("material.remove_material", model, material=x)
    
for x in model.by_type("IfcSurfaceStyle"):
    print("IfcSurfaceStyle wurde entfernt.")
    ifcopenshell.api.run("style.remove_style", model, style=x)
    


#Schritt 4: Zusammenfassen duplizierter Typen
print("Schritt 4: Zusammenfassen duplizierter Typen")
ifcpatch.execute({"input": model, "file": model, "recipe": "MergeDuplicateTypes", "arguments": []})


#Schritt 5: Zusammenfassen einzelner Bauteilkomponenten zu Bauteilen
print("Schritt 5: Zusammenfassen einzelner Bauteilkomponenten zu Bauteilen")

O = 0., 0., 0.
X = 1., 0., 0.
Y = 0., 1., 0.
Z = 0., 0., 1.

# Creates an IfcAxis2Placement3D from Location, Axis and RefDirection specified as Python tuples
def create_ifcaxis2placement(ifcfile, point=O, dir1=Z, dir2=X):
    point = ifcfile.createIfcCartesianPoint(point)
    dir1 = ifcfile.createIfcDirection(dir1)
    dir2 = ifcfile.createIfcDirection(dir2)
    axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement

# Creates an IfcLocalPlacement from Location, Axis and RefDirection, specified as Python tuples, and relative placement
def create_ifclocalplacement(ifcfile, point=O, dir1=Z, dir2=X, relative_to=None):
    axis2placement = create_ifcaxis2placement(ifcfile,point,dir1,dir2)
    ifclocalplacement2 = ifcfile.createIfcLocalPlacement(relative_to,axis2placement)
    return ifclocalplacement2

for x in model.by_type("IfcElement"):
    print("Betrachtetes Element: " + str(x.is_a()))
    element_class = x.is_a()
    psets = ifcopenshell.util.element.get_psets(x)
    if "SIB-BW-IDENT" in psets.keys():
        ident = selector.get_element_value(x, "SIB-BW-IDENT.IDENT")
        same_ident = selector.parse(model, '.' + str(element_class) + '[SIB-BW-IDENT.IDENT = "' + str(ident) + '"]')
        
        if len(same_ident) > 1:
            aggregation = ifcopenshell.api.run("root.create_entity", model, ifc_class=element_class)
            
            if x.ContainedInStructure != ():
                spatialStructure = x.ContainedInStructure[0].RelatingStructure
                spStr_placement = spatialStructure.ObjectPlacement
                el_placement = create_ifclocalplacement(model, relative_to=spStr_placement)
                
                ifcopenshell.api.run("attribute.edit_attributes", model, product=aggregation, attributes={"Name": "Aggregation", "ObjectPlacement":el_placement})
                ifcopenshell.api.run("spatial.assign_container", model, product=aggregation, relating_structure=spatialStructure)
                
                psetNew = ifcopenshell.api.run("pset.add_pset", model, product=aggregation, name="SIB-BW-IDENT")
                ifcopenshell.api.run("pset.edit_pset", model, pset=psetNew, properties=psets["SIB-BW-IDENT"])
                    
            for y in same_ident:
                ifcopenshell.api.run("aggregate.assign_object", model, product=y, relating_object=aggregation)
                print(str(y) + " wurde " + str(aggregation) + " hinzugefuegt.")
                yPsets = ifcopenshell.util.element.get_psets(y)
                yPset = model.by_id(int(yPsets["SIB-BW-IDENT"]["id"]))
                ifcopenshell.api.run("pset.remove_pset", model, product=y, pset=yPset)
                    
  
#Schritt 6: Einlesen der DBF-Dateien

gruend = [
OrderedDict([('ART', 160011200000000), ('TYP', 'Flachgründung mit Sauberkeitsschicht'), ('ORT', 'Fundament A10***'), ('JAHR', 2021), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130011910000000), ('GRUENDNR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 10, 14, 7, 25)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8K0TX2FC'), ('AMT', '00990X'), ('REF_GRUND', '8K0TX2FB'), ('ID_NR', '1234567 0'), ('_NullFlags', b'\x00')]),
OrderedDict([('ART', 160011200000000), ('TYP', 'Flachgründung mit Sauberkeitsschicht'), ('ORT', 'Fundament A20***'), ('JAHR', 2021), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130011910000000), ('GRUENDNR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 10, 14, 16, 8, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8K0UKS44'), ('AMT', '00990X'), ('REF_GRUND', '8K0UKS45'), ('ID_NR', '1234567 0'), ('_NullFlags', b'\x00')])
]
#gruend = DBF(r'C:\Users\user\Desktop\DA_Daten\Bauwerksbuch\BWB\gruend.DBF', load=True)


kappen = [
OrderedDict([('ORT', 'links (Südost)***'), ('KONSTRUKT', 220021000000000), ('VERANKER', 220033000000000), ('GR_BLOCKL', 0.0), ('BREITE', 1.75), ('BAUJAHR', 2021), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('KAPPENNR', 1), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 7, 52, 23, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0KQOSS'), ('AMT', '00990X'), ('LAENGE', 41.0), ('REF_KAPPEN', '8L0KQOSR'), ('ID_NR', '1234567 0'), ('_NullFlags', b'\x00')]),
OrderedDict([('ORT', 'rechts (Nordwest)***'), ('KONSTRUKT', 220021000000000), ('VERANKER', 220033000000000), ('GR_BLOCKL', 0.0), ('BREITE', 1.75), ('BAUJAHR', 2021), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('KAPPENNR', 1), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 7, 52, 43)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0L6A8G'), ('AMT', '00990X'), ('LAENGE', 41.0), ('REF_KAPPEN', '8L0L6A8H'), ('ID_NR', '1234567 0'), ('_NullFlags', b'\x00')])
]
#kappen = DBF(r'C:\Users\user\Desktop\DA_Daten\Bauwerksbuch\BWB\kappen.DBF', load=True)

schutz = [
OrderedDict([('ART', 230013430000000), ('ORT', 'Kappe links (Südost) ***'), ('BAUJAHR', 2021), ('LAENGE', 10.0), ('HOEHE_FB', 1.8), ('BEMERKUNG', 'inkl. Handlauf nach RiZ Gel 9***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('SCHUTZ_NR', 2), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 8, 20, 21, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0NRY6Y'), ('AMT', '00990X'), ('REF_SCHUTZ', '8L0NRY6X'), ('ID_NR', '1234567 0'), ('AUFHALTEST', None), ('ANPRALLHEF', None), ('WIRKBERKL', None), ('HERSTELLER', ''), ('SYSTEM', None), ('_NullFlags', b'\xe0\x02')]),
OrderedDict([('ART', 230013430000000), ('ORT', 'Kappe rechts (Nordwest)***'), ('BAUJAHR', 2021), ('LAENGE', 10.0), ('HOEHE_FB', 1.8), ('BEMERKUNG', 'inkl. Handlauf nach RiZ Gel 9***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('SCHUTZ_NR', 2), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 8, 20, 35, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0NXEIA'), ('AMT', '00990X'), ('REF_SCHUTZ', '8L0NXEIB'), ('ID_NR', '1234567 0'), ('AUFHALTEST', None), ('ANPRALLHEF', None), ('WIRKBERKL', None), ('HERSTELLER', ''), ('SYSTEM', None), ('_NullFlags', b'\xe0\x02')]),
OrderedDict([('ART', 230012111000000), ('ORT', 'Kappe links (Südost) / Flügelbereich A10***'), ('BAUJAHR', 2021), ('LAENGE', 15.77), ('HOEHE_FB', 1.0), ('BEMERKUNG', 'Füllstabgeländer nach RiZ Gel 4, 9, 10, 14***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('SCHUTZ_NR', 3), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 7, 56, 42)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0PQ068'), ('AMT', '00990X'), ('REF_SCHUTZ', '8L0PQ067'), ('ID_NR', '1234567 0'), ('AUFHALTEST', None), ('ANPRALLHEF', None), ('WIRKBERKL', None), ('HERSTELLER', ''), ('SYSTEM', None), ('_NullFlags', b'\xe0\x02')]),
OrderedDict([('ART', 230012111000000), ('ORT', 'Kappe links (Südost) / Flügelbereich A20***'), ('BAUJAHR', 2021), ('LAENGE', 14.69), ('HOEHE_FB', 1.0), ('BEMERKUNG', 'Füllstabgeländer nach RiZ Gel 4, 9, 10, 14***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('SCHUTZ_NR', 3), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 7, 56, 58, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0T4Z74'), ('AMT', '00990X'), ('REF_SCHUTZ', '8L0T4Z75'), ('ID_NR', '1234567 0'), ('AUFHALTEST', None), ('ANPRALLHEF', None), ('WIRKBERKL', None), ('HERSTELLER', ''), ('SYSTEM', None), ('_NullFlags', b'\xe0\x02')]),
OrderedDict([('ART', 230012111000000), ('ORT', 'Kappe rechts (Nordwest) / Flügelbereich A10***'), ('BAUJAHR', 2021), ('LAENGE', 13.89), ('HOEHE_FB', 1.0), ('BEMERKUNG', 'Füllstabgeländer nach RiZ Gel 4, 9, 10, 14***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('SCHUTZ_NR', 3), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 7, 57, 12, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0T7LSX'), ('AMT', '00990X'), ('REF_SCHUTZ', '8L0T7LSY'), ('ID_NR', '1234567 0'), ('AUFHALTEST', None), ('ANPRALLHEF', None), ('WIRKBERKL', None), ('HERSTELLER', ''), ('SYSTEM', None), ('_NullFlags', b'\xe0\x02')]),
OrderedDict([('ART', 230012111000000), ('ORT', 'Kappe rechts (Nordwest) / Flügelbereich A20***'), ('BAUJAHR', 2021), ('LAENGE', 15.72), ('HOEHE_FB', 1.0), ('BEMERKUNG', 'Füllstabgeländer nach RiZ Gel 4, 9, 10, 14***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 130000000000000), ('SCHUTZ_NR', 3), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 7, 57, 26)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0T9CJL'), ('AMT', '00990X'), ('REF_SCHUTZ', '8L0T9CJM'), ('ID_NR', '1234567 0'), ('AUFHALTEST', None), ('ANPRALLHEF', None), ('WIRKBERKL', None), ('HERSTELLER', ''), ('SYSTEM', None), ('_NullFlags', b'\xe0\x02')]),
]
#schutz = DBF(r'C:\Users\user\Desktop\DA_Daten\Bauwerksbuch\BWB\schutz.DBF', load=True)

baustoffe = [
OrderedDict([('BAUTEILNR', 130021210000000), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054210000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021310000000), ('ZEMENTGEHL', 350), ('ZUSCHLAG', 'Sand, Kies, Splitt***'), ('BETONZUS', 'P-hit 45 (BV)\r\nP-hit RC 671 (BV/FM) ***'), ('OBERFL', 320066000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 9, 49, 2)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8K0U9Q04'), ('ID_KONST', None), ('REF_BAUST', '8K0U9Q03'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', '8K0TX2FB'), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XA 2 - XC 4 - XD 2 - XF 3 - XM 1'), ('KONSISTENZ', 320184000000000), ('KORNGROES', 320175000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xd8\xff\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130021210000000), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054210000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021310000000), ('ZEMENTGEHL', 350), ('ZUSCHLAG', 'Sand, Kies, Splitt***'), ('BETONZUS', 'P-hit 45 (BV)\r\nP-hit RC 671 (BV/FM) ***'), ('OBERFL', 320066000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 9, 49, 14, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8K0UKSJC'), ('ID_KONST', None), ('REF_BAUST', '8K0UKSJB'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', '8K0UKS45'), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XA 2 - XC 4 - XD 2 - XF 3 - XM 1'), ('KONSISTENZ', 320184000000000), ('KORNGROES', 320175000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xd8\xff\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130021800000000), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054150000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021251000000), ('ZEMENTGEHL', 360), ('ZUSCHLAG', 'Sand, Kies***'), ('BETONZUS', 'P-por 2000 (LP)\r\nP-hit RC 671 (BV/FM)***'), ('OBERFL', 320061000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 9, 51, 3, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0KXDOO'), ('ID_KONST', None), ('REF_BAUST', '8L0KXDON'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', '8L0KQOSR'), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XC 4 - XD 3 - XF 4'), ('KONSISTENZ', 320183000000000), ('KORNGROES', 320173000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf8\xfd\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130021800000000), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054150000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021251000000), ('ZEMENTGEHL', 360), ('ZUSCHLAG', 'Sand, Kies***'), ('BETONZUS', 'P-por 2000 (LP)\r\nP-hit RC 671 (BV/FM)***'), ('OBERFL', 320061000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 9, 52, 46)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0L6AR6'), ('ID_KONST', None), ('REF_BAUST', '8L0L6AR5'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', '8L0L6A8H'), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XC 4 - XD 3 - XF 4'), ('KONSISTENZ', 320183000000000), ('KORNGROES', 320173000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf8\xfd\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130022134000000), ('HBST', 320015000000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 0), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 0), ('ZEMENTGEHL', None), ('ZUSCHLAG', ' ***'), ('BETONZUS', ' ***'), ('OBERFL', 0), ('L_FIRMA', 'Firma B, Stadt B'), ('BETONSTAHL', 0), ('FERTIGT', 0), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 11, 9, 43, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0NUQ5C'), ('ID_KONST', None), ('REF_BAUST', '8L0NUQ5B'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', '8L0NRY6X'), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', ''), ('KONSISTENZ', 0), ('KORNGROES', 0), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf9\xf7\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130022134000000), ('HBST', 320015000000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 0), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 0), ('ZEMENTGEHL', None), ('ZUSCHLAG', ' ***'), ('BETONZUS', ' ***'), ('OBERFL', 0), ('L_FIRMA', 'Firma B, Stadt B'), ('BETONSTAHL', 0), ('FERTIGT', 0), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 11, 9, 49, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0NXEYU'), ('ID_KONST', None), ('REF_BAUST', '8L0NXEYT'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', '8L0NXEIB'), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', ''), ('KONSISTENZ', 0), ('KORNGROES', 0), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf9\xf7\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130022121110000), ('HBST', 320012131000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 0), ('STAHLGUTE', 320122100000000), ('HOLZGUTE', 0), ('VERBIND_M', 320141000000000), ('ZEMENT', 0), ('ZEMENTGEHL', None), ('ZUSCHLAG', ' ***'), ('BETONZUS', ' ***'), ('OBERFL', 0), ('L_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BETONSTAHL', 0), ('FERTIGT', 0), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 13, 28, 10, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0SIDVI'), ('ID_KONST', None), ('REF_BAUST', '8L0SIDVH'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', '8L0PQ067'), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', ''), ('KONSISTENZ', 0), ('KORNGROES', 0), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf9\xf7\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130022121110000), ('HBST', 320012131000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 0), ('STAHLGUTE', 320122100000000), ('HOLZGUTE', 0), ('VERBIND_M', 320141000000000), ('ZEMENT', 0), ('ZEMENTGEHL', None), ('ZUSCHLAG', ' ***'), ('BETONZUS', ' ***'), ('OBERFL', 0), ('L_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BETONSTAHL', 0), ('FERTIGT', 0), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 13, 35, 41, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0T4ZML'), ('ID_KONST', None), ('REF_BAUST', '8L0T4ZMK'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', '8L0T4Z75'), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', ''), ('KONSISTENZ', 0), ('KORNGROES', 0), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf9\xf7\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130022121110000), ('HBST', 320012131000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 0), ('STAHLGUTE', 320122100000000), ('HOLZGUTE', 0), ('VERBIND_M', 320141000000000), ('ZEMENT', 0), ('ZEMENTGEHL', None), ('ZUSCHLAG', ' ***'), ('BETONZUS', ' ***'), ('OBERFL', 0), ('L_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BETONSTAHL', 0), ('FERTIGT', 0), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 13, 37, 44)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0T7MA1'), ('ID_KONST', None), ('REF_BAUST', '8L0T7MA0'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', '8L0T7LSY'), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', ''), ('KONSISTENZ', 0), ('KORNGROES', 0), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf9\xf7\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130022121110000), ('HBST', 320012131000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 0), ('STAHLGUTE', 320122100000000), ('HOLZGUTE', 0), ('VERBIND_M', 320141000000000), ('ZEMENT', 0), ('ZEMENTGEHL', None), ('ZUSCHLAG', ' ***'), ('BETONZUS', ' ***'), ('OBERFL', 0), ('L_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BETONSTAHL', 0), ('FERTIGT', 0), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 11, 13, 39, 4, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8L0T9CYU'), ('ID_KONST', None), ('REF_BAUST', '8L0T9CYT'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', '8L0T9CJM'), ('REF_LAGER', ''), ('REF_BRUCKE', ''), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', ''), ('KONSISTENZ', 0), ('KORNGROES', 0), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf9\xf7\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130011910000000), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054210000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021310000000), ('ZEMENTGEHL', 361), ('ZUSCHLAG', 'Sand, Kies***'), ('BETONZUS', 'BV 45\r\nRC 671***'), ('OBERFL', 320061000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 1, 12, 13, 25, 45)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8M0SO2IX'), ('ID_KONST', None), ('REF_BAUST', '8M0SO2IW'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', '8K0SSI8M'), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XA 2 - XC 4 - XD 2 - XF 3 - XM 1'), ('KONSISTENZ', 320184000000000), ('KORNGROES', 320173000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf8\xdf\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130011131425100), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054210000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021310000000), ('ZEMENTGEHL', 358), ('ZUSCHLAG', 'Sand, Kies***'), ('BETONZUS', 'BV 45\r\nPantarhol VZ 85***'), ('OBERFL', 320061000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 2), ('BEARB_DAT', datetime.datetime(2022, 1, 12, 13, 33, 51, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8M0SSMJC'), ('ID_KONST', None), ('REF_BAUST', '8M0SSMJB'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', '8K0SSI8M'), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XA 2 - XC 4 - XD 2 - XF 3 - XM 1'), ('KONSISTENZ', 320183000000000), ('KORNGROES', 320173000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf8\xdf\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130000000000000), ('HBST', 320011200000000), ('IS_HBST_UB', 0), ('FESTIGKEIT', 320054220000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021310000000), ('ZEMENTGEHL', 380), ('ZUSCHLAG', 'Sand, Kies***'), ('BETONZUS', 'BV 45\r\nP-hit RC 671 (BV/FM)***'), ('OBERFL', 320061000000000), ('L_FIRMA', 'Beton Firma, Werk Stadt A'), ('BETONSTAHL', 320071620000000), ('FERTIGT', 320082000000000), ('BEMERKUNG', 'Bauteil: Aufbeton***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 3), ('BEARB_DAT', datetime.datetime(2022, 2, 10, 14, 4, 54, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8M0T2XU5'), ('ID_KONST', None), ('REF_BAUST', '8M0T2XU4'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', '8K0SSI8M'), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XA 2 - XC 4 - XD 2 - XF 3'), ('KONSISTENZ', 320184000000000), ('KORNGROES', 320173000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf8\xdf\xf7\xff\x01')]),
OrderedDict([('BAUTEILNR', 130000000000000), ('HBST', 320011211000000), ('IS_HBST_UB', 1), ('FESTIGKEIT', 320054220000000), ('STAHLGUTE', 0), ('HOLZGUTE', 0), ('VERBIND_M', 0), ('ZEMENT', 320021100000000), ('ZEMENTGEHL', 350), ('ZUSCHLAG', 'stoneash II***'), ('BETONZUS', 'ACE 420 ***'), ('OBERFL', 320061000000000), ('L_FIRMA', 'Bau GmbH D, Stadt D'), ('BETONSTAHL', 320071200000000), ('FERTIGT', 320081000000000), ('BEMERKUNG', ' ***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUST_NR', 4), ('BEARB_DAT', datetime.datetime(2022, 5, 25, 9, 48, 0, 999000)), ('BEARBEITER', 'SIBUSER'), ('IDENT', '8M0TA4RZ'), ('ID_KONST', None), ('REF_BAUST', '8M0TA4RY'), ('AMT', '00990X'), ('REF_VSPANN', ''), ('REF_GRUND', ''), ('REF_ANKER', ''), ('REF_SEILE', ''), ('REF_UBGKON', ''), ('REF_KAPPEN', ''), ('REF_AUSSTA', ''), ('REF_SCHUTZ', ''), ('REF_LAGER', ''), ('REF_BRUCKE', '8K0SSI8M'), ('REF_VKZBRU', ''), ('REF_TUNNEL', ''), ('REF_SON_BW', ''), ('REF_STZ_SG', ''), ('REF_LRM_SG', ''), ('HERKUNFT', ''), ('ID_NR', '1234567 0'), ('EXPOSITION', 'XA 2 - XC 4 - XD 2 - XF 3 - XS 2'), ('KONSISTENZ', 320185000000000), ('KORNGROES', 320173000000000), ('PROD_BEZ', ''), ('ZUG_FSTG_L', None), ('ZUG_FSTG_Q', None), ('ZUG_K_DH_L', None), ('ZUG_K_DH_Q', None), ('FL_MASSE', None), ('GEOTX_R_KL', None), ('WASS_DRCHL', None), ('WASS_ABLT', None), ('STMP_DKRFT', None), ('OEFF_WEIT', None), ('ROHSTOFF', 0), ('D_SCHL_VRH', None), ('DICKE_GWB', None), ('SCHTZ_WRKS', None), ('ANF_KL', ''), ('_NullFlags', b'\xf8\xdf\xf7\xff\x01')])
]
#baustoffe = DBF(r'C:\Users\user\Desktop\DA_Daten\Bauwerksbuch\BWB\baustoffe.DBF', load=True)

korr_sys = [
OrderedDict([('BT_OBERFL', 300013000000000), ('OBERFL_VRB', 300026000000000), ('BINDM_GR', 300034100000000), ('PIGM_GR', 300046000000000), ('BINDM_DK', 300056000000000), ('PIGM_DK', 300065100000000), ('ANZ_GR', 1), ('ANZ_DECKBE', 2), ('GESSCHICHT', 240), ('APPLIKAT', 300107000000000), ('ORT', 'Füllstabgeländer ***'), ('DICHTSTOFF', 0), ('INJ_STOFF', 0), ('AUSF_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BEZEICHN', 'Korrosionsschutz'), ('BAUJAHR', 2021), ('BESCH_FL', 14), ('BEMERKUNG', 'ZB: DB 703 687.17 (grau) \r\nDB: CHING-Deckbeschichtung RAL 3003***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 0), ('BESCH_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 5, 17, 10, 54, 15, 999000)), ('BEARBEITER', 'SIBUSER'), ('REF_BAUST', '8L0SIDVH'), ('ID_NR', '1234567 0'), ('IDENT', '8L0SMRYB'), ('AMT', '00990X'), ('ART_KORRS', 300191131110000), ('KORRSCHUTZ', 300201000000000), ('BINDEM_ZB', 300215100000000), ('PIGM_ZB', 300221000000000), ('_NullFlags', b'\x00')]),
OrderedDict([('BT_OBERFL', 300013000000000), ('OBERFL_VRB', 300026000000000), ('BINDM_GR', 300034100000000), ('PIGM_GR', 300046000000000), ('BINDM_DK', 300056000000000), ('PIGM_DK', 300065100000000), ('ANZ_GR', 1), ('ANZ_DECKBE', 2), ('GESSCHICHT', 240), ('APPLIKAT', 300107000000000), ('ORT', 'Füllstabgeländer ***'), ('DICHTSTOFF', 0), ('INJ_STOFF', 0), ('AUSF_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BEZEICHN', 'Korrosionsschutz'), ('BAUJAHR', 2021), ('BESCH_FL', 16), ('BEMERKUNG', 'ZB: DB 703 687.17 (grau) \r\nDB: CHING-Deckbeschichtung RAL 3003***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 0), ('BESCH_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 5, 17, 10, 54, 55)), ('BEARBEITER', 'SIBUSER'), ('REF_BAUST', '8L0T4ZMK'), ('ID_NR', '1234567 0'), ('IDENT', '8L0T505B'), ('AMT', '00990X'), ('ART_KORRS', 300191131110000), ('KORRSCHUTZ', 300201000000000), ('BINDEM_ZB', 300215100000000), ('PIGM_ZB', 300221000000000), ('_NullFlags', b'\x00')]),
OrderedDict([('BT_OBERFL', 300013000000000), ('OBERFL_VRB', 300026000000000), ('BINDM_GR', 300034100000000), ('PIGM_GR', 300046000000000), ('BINDM_DK', 300056000000000), ('PIGM_DK', 300065100000000), ('ANZ_GR', 1), ('ANZ_DECKBE', 2), ('GESSCHICHT', 240), ('APPLIKAT', 300107000000000), ('ORT', 'Füllstabgeländer ***'), ('DICHTSTOFF', 0), ('INJ_STOFF', 0), ('AUSF_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BEZEICHN', 'Korrosionsschutz'), ('BAUJAHR', 2021), ('BESCH_FL', 15), ('BEMERKUNG', 'ZB: DB 703 687.17 (grau) \r\nDB: CHING-Deckbeschichtung RAL 3003***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 0), ('BESCH_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 5, 17, 10, 56, 22, 999000)), ('BEARBEITER', 'SIBUSER'), ('REF_BAUST', '8L0T7MA0'), ('ID_NR', '1234567 0'), ('IDENT', '8L0T7MQ4'), ('AMT', '00990X'), ('ART_KORRS', 300191131110000), ('KORRSCHUTZ', 300201000000000), ('BINDEM_ZB', 300215100000000), ('PIGM_ZB', 300221000000000), ('_NullFlags', b'\x00')]),
OrderedDict([('BT_OBERFL', 300013000000000), ('OBERFL_VRB', 300026000000000), ('BINDM_GR', 300034100000000), ('PIGM_GR', 300046000000000), ('BINDM_DK', 300056000000000), ('PIGM_DK', 300065100000000), ('ANZ_GR', 1), ('ANZ_DECKBE', 2), ('GESSCHICHT', 240), ('APPLIKAT', 300107000000000), ('ORT', 'Füllstabgeländer ***'), ('DICHTSTOFF', 0), ('INJ_STOFF', 0), ('AUSF_FIRMA', ' Bauschlosserei & Maschinenbau Firma C, Stadt C'), ('BEZEICHN', 'Korrosionsschutz'), ('BAUJAHR', 2021), ('BESCH_FL', 16), ('BEMERKUNG', 'ZB: DB 703 687.17 (grau) \r\nDB: CHING-Deckbeschichtung RAL 3003***'), ('BWNR', '1234567'), ('TEIL_BWNR', ' 0'), ('BAUTEILNR', 0), ('BESCH_NR', 1), ('BEARB_DAT', datetime.datetime(2022, 5, 17, 10, 57, 34)), ('BEARBEITER', 'SIBUSER'), ('REF_BAUST', '8L0T9CYT'), ('ID_NR', '1234567 0'), ('IDENT', '8L0T9DG8'), ('AMT', '00990X'), ('ART_KORRS', 300191131110000), ('KORRSCHUTZ', 300201000000000), ('BINDEM_ZB', 300215100000000), ('PIGM_ZB', 300221000000000), ('_NullFlags', b'\x00')])
]
#korr_sys = DBF(r'C:\Users\user\Desktop\DA_Daten\Bauwerksbuch\BWB\korr_sys.DBF', load=True)


#Schritt 6.1 und 6.2

dateiList = OrderedDict([('\gruend.DBF', gruend), ('\kappen.DBF', kappen), ('\schutz.DBF', schutz)])


for datei in dateiList.keys():
    table = dateiList[datei]
    gruppenName = "Bauteilgruppe"
    if datei == "\gruend.DBF":
        gruppenName = "Gründungen"
    elif datei == "\kappen.DBF":
        gruppenName = "Kappen"
    elif datei == "\schutz.DBF":
        gruppenName = "Schutzeinrichtungen"
    
    group = ifcopenshell.api.run("group.add_group", model, Name=gruppenName)
    
    liste = []
    
    for r in table:    
        for x in model.by_type("IfcElement"):
            psets = ifcopenshell.util.element.get_psets(x)
            if "SIB-BW-IDENT" in psets.keys():
                ident = selector.get_element_value(x, "SIB-BW-IDENT.IDENT")
                if ident == r['IDENT']:
                    dict = {}
                    for temp in r.keys():
                        dict[str(temp)] = str(r[temp])
                    pset = ifcopenshell.api.run("pset.add_pset", model, product=x, name="ASB-ING-Bauteil")
                    ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties=dict)
                    liste.append(x)
                    break
    print(liste)
    ifcopenshell.api.run("group.assign_group", model, products=liste, group=group)
            

#Diese Angaben muessen haendisch eingetragen werden
group = ifcopenshell.api.run("group.add_group", model, Name="Unterbau")
liste = selector.parse(model, '.IfcWall[SIB-BW-IDENT.IDENT = "WDLA10"] | .IfcWall[SIB-BW-IDENT.IDENT = "WDLA20"]')
ifcopenshell.api.run("group.assign_group", model, products=liste, group=group)


group = ifcopenshell.api.run("group.add_group", model, Name="Überbau")
liste = selector.parse(model, '.IfcSlab[SIB-BW-IDENT.IDENT = "PLORTB"] | .IfcBeam[SIB-BW-IDENT.IDENT = "HTXXFT"] | .IfcWall[SIB-BW-IDENT.IDENT = "ALKOA10"] | .IfcWall[SIB-BW-IDENT.IDENT = "ALKOA20"]')
ifcopenshell.api.run("group.assign_group", model, products=liste, group=group)




#Schritt 6.3: Erstellen und Zuweisen der Materialien inklusive Korrosionsschutz

myList = ["8M0SO2IX", "8K0U9Q04", "8M0SO2IX", "8K0UKSJC", "8L0KXDOO", "8L0L6AR6", "8M0T2XU5", "8M0TA4RZ", "8L0SIDVI", "8L0T7MA1", "8L0T4ZML", "8L0T9CYU", "8L0NUQ5C", "8L0NXEYU", "8M0SSMJC", "8M0SSMJC"]

for record in baustoffe:
    if myList.count(record['IDENT']) > 0:
        material = ifcopenshell.api.run("material.add_material", model, name=str(record['IDENT']), category="SIB-BW")
        dict = {}
        for temp in record.keys():
            if record[temp] != "":
                dict[str(temp)] = str(record[temp])
        pset = ifcopenshell.api.run("pset.add_pset", model, product=material, name="ASB-ING-Material")
        ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties=dict)


for x in model.by_type("IfcElement"):
        psets = ifcopenshell.util.element.get_psets(x)
        if "SIB-BW-IDENT" in psets.keys():
            matIdent = selector.get_element_value(x, "SIB-BW-IDENT.Baustoff-IDENT")
            ifcMat= selector.parse(model, '.IfcMaterial[ASB-ING-Material.IDENT = "' + str(matIdent) + '"]')
            if ifcMat != []:
                if len(ifcMat) == 1:
                    ifcopenshell.api.run("material.assign_material", model, product=x, material=ifcMat[0])
                elif len(ifcMat) == 2:
                    ifcopenshell.api.run("material.assign_material", model, product=x, material=ifcMat[0])
                    ifcopenshell.api.run("material.assign_material", model, product=x, material=ifcMat[1])


#Korrosionsschutz 

for x in korr_sys:
    refBaust = x['REF_BAUST']
    korrMat = selector.parse(model, '.IfcMaterial[ASB-ING-Material.REF_BAUST = "' + str(refBaust) + '"]')
    if korrMat != []:
        dict = {}
        for temp in x.keys():
            dict[str(temp)] = str(x[temp])
            pset = ifcopenshell.api.run("pset.add_pset", model, product=korrMat[0], name="ASB-ING-Korrosion")
            ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties=dict)
    




model.write(r"C:\Users\user\Desktop\DA_Daten\FBI_Paper\Final\Modell_Bruecke_FBI2023_V2.ifc")
print("Abgeschlossen")
