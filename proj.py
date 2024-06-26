# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 17:06:41 2024

@author: user
"""

from math import *
import numpy as np
from argparse import ArgumentParser

class Transformacje:
    def __init__(self, model: str = "WGS84"):
        """
        Parametry elipsoid:
            a - duża półoś elipsoidy
            e2 - mimośród^2
        """
        if model == "WGS84":
            self.a = 6378137.0 
            self.e2 = 0.00669437999014
        elif model == "GRS80":
            self.a = 6378137.0
            self.e2 = 0.0066943800229
        elif model == "KRASOWSKI":
            self.a = 6378245.0
            self.e2 =  0.00669342162296
       # else:
           # raise NotImplementedError(f"Program nie obsługuje podanej elipsoidy")
        
    """Fukcje, które są niezbędne do transformacji"""
        
    def Np(self, fi):    #promień krzywizny w I wertykale
        N = self.a / np.sqrt(1 - self.e2 * np.sin(fi)**2)
        return(N)

    def Sigma(self, fi):
        A0 = 1 - (self.e2/4) - (3*(self.e2)**2)/64 -  (5*(self.e2)**3)/256
        A2 = 3/8 * (self.e2 + (self.e2)**2/4 + 15*(self.e2)**3/128)
        A4 = 15/256 * ( (self.e2)**2 + (3*((self.e2)**3))/4 )
        A6 = 35 * (self.e2)**3 / 3072
        sigma = self.a * ( A0 * fi - A2 * np.sin(2*fi) + A4 * np.sin(4*fi) - A6 * np.sin(6*fi) )
               
        return(sigma)
        
        
    """Tranformacja współrzędnych geocentrycznych XYZ na współrzędne elipsoidalne fi, lambda, h"""
        
    def XYZ2flh(self, X, Y, Z):   # Algorytm Hirvonena
       """
       Parametry
       ----------
       współrzedne geocentryczne punktu [m]
       X Y Z 
       
       Wynik
       -------
       współrzędne elipsoidalne punktu
       fi : szerokosć geodezyjna punktu [rad]
       lam : długosć geodezyjna punktu [rad]
       h : wysokosć punktu [m]
       """
       flh = []
       for x, y, z in zip(X, Y, Z):
           r = np.sqrt(x**2 + y**2)  # promień
           fi = np.arctan(z / (r * (1 - self.e2)))
           while True:
               N = self.Np(fi)
               h = (r / np.cos(fi)) - N
               fp = fi
               fi = np.arctan(z / (r * (1 - self.e2 * N / (N + h))))
               if abs(fp - fi) < (0.000001 / 206265):
                   break
           l = np.arctan2(y, x)
           flh.append([np.rad2deg(fi), np.rad2deg(l), h])
       return flh
        
        
    """Transformacja współrzędnych elipsoidalnych fi, lambda, h na współrzędne geocentryczne XYZ"""
        
    def flh2XYZ(self, fi, lam, h):
        """
        Parametry
        ----------
        współrzędne elipsoidalne punktu
        fi : szerokosć geodezyjna punktu [rad]
        lam : długosć geodezyjna punktu [rad]
        h : wysokosć punktu [m]
        
        Wynik
        -------
        współrzedne geocentryczne punktu [m]
        X Y Z
        """
        XYZ = []
        for fi, lam, h in zip(fi, lam, h):
                N = self.Np(fi)
                X = (N + h) * np.cos(fi) * np.cos(lam)
                Y = (N + h) * np.cos(fi) * np.sin(lam)
                Z = (N * (1 - self.e2) + h) * np.sin(fi)

        XYZ.append([X, Y, Z])
        return(XYZ)
       
    """Tranformacja współrzędnych geocentrycznych do współrzędnych topocentrycznych"""
     

    def XYZ2NEU(self, X, Y, Z, X0, Y0, Z0):
        """
        Parametry
        ----------
        współrzedne geocentryczne satelitów [m]
            X Y Z 
        wsporedne geocentryczne anteny [m]
            X0 Y0 Z0
        Wynik
        -------
        Współrzędne geodezyjne w układzie topocentrycznym [m]
        X Y Z
        
        """

        wynik = []
        for X0, Y0, Z0 in zip(X0, Y0, Z0):
            lam = np.arctan2(Y0, X0)
            r = np.sqrt(X0**2+Y0**2)
            fi = np.arctan(Z0 / (r * (1 - self.e2)))

            while True:
                N = self.Np(fi)
                h = (r/np.cos(fi))-N
                fp = fi
                fi = np.arctan(Z0/(r*(1-self.e2 * N/(N+h))))
                if abs(fp-fi)<(0.000001/206265):
                    break
                
            
        R_neu = np.array([[-np.sin(fi)*np.cos(lam), -np.sin(lam), np.cos(fi)*np.cos(lam)],
                         [-np.sin(fi)*np.sin(lam), np.cos(lam), np.cos(fi)*np.sin(lam)],
                         [np.cos(fi), 0, np.sin(fi)]])
                
        X_list = []
        Y_list = []
        Z_list = []
        for X, Y, Z in zip(X, Y, Z):
            X_list.append(X)
            Y_list.append(Y)
            Z_list.append(Z)

        X_list = np.array(X_list)
        Y_list = np.array(Y_list)
        Z_list = np.array(Z_list)

        xyz = np.column_stack([np.reshape(X_list, (len(X_list), 1)), np.reshape(
            Y_list, (len(Y_list), 1)), np.reshape(Z_list, (len(Z_list), 1))])

        xyz0 = np.array([X0, Y0, Z0]).T

        xyzt = xyz-xyz0

        neu = R_neu.T @ xyzt.T
        wynik.append(neu.T)        

        return wynik
        
    """Tranformacja współrzędnych elipsoidalnych fi, lambda do współrzędnych w układzie 2000"""
          
    def fl22000(self, fi, lam):
        """
        Parametry
        ----------
        współrzędne elipsoidalne punktu
        fi : szerokosć geodezyjna punktu [rad]
        lam : długosć geodezyjna punktu [rad]
        h : wysokosć punktu [m]
        
        Wynik
        -------
        współrzedne geocentryczne punktu w układzie PL-2000 [m]
        X Y 
        """
        m0 = 0.999923
        wsp2000 = []
        for fi, lam in zip(fi,lam):
            lam0 = 0 
            strefa = 0
            if lam > np.deg2rad(13.5) and lam < np.deg2rad(16.5):
                strefa = 5
                lam0 = np.deg2rad(15)
            elif lam > np.deg2rad(16.5) and lam < np.deg2rad(19.5):
                strefa = 6
                lam0 = np.deg2rad(18)
            elif lam > np.deg2rad(19.5) and lam < np.deg2rad(22.5):
                strefa =7
                lam0 = np.deg2rad(21)
            elif lam > np.deg2rad(22.5) and lam < np.deg2rad(25.5):
                strefa = 8
                lam0 = np.deg2rad(24)
            else:
                print("Punkt poza strefami odwzorowawczymi układu PL-2000")
                continue
                         
            b2 = (self.a**2)*(1-self.e2)    
            ep2 = (self.a**2-b2)/b2   #drugi mimosrod elipsy   #drugi mimosrod elipsy
            dlam = lam - lam0
            t = np.tan(fi)
            n = np.sqrt(ep2 * (np.cos(fi))**2)
            N = self.Np(fi)
            sigma = self.Sigma(fi)
            
            XGK =  sigma    +    ( ((dlam**2/2)*N*np.sin(fi)*np.cos(fi))    *    (1   +   ((dlam**2/12)*(np.cos(fi)**2)*(5 - t**2 + 9*n**2 + 4*n**4))      +         ((dlam**4/360)*(np.cos(fi)**4)*(61 - 58*t**2 + t**4 + 270*n**2 - 330*n**2*t**2))))
            YGK =  (dlam* N * np.cos(fi))  *   ( 1 +  ((dlam**2/6)   *   (np.cos(fi)**2)   *  (1 - t**2 + n**2))     +     (((dlam**4/120)*(np.cos(fi)**4)) * (5 - (18*t**2) + t**4 + (14 * n**2) - (58*n**2*t**2))))
            
            X2000 = XGK * m0
            Y2000 = YGK * m0 + strefa*1000000 + 500000
            wsp2000.append([X2000, Y2000])
                
        return(wsp2000) 
        
        
    """Tranformacja współrzędnych fi, lambda do współrzędnych w układzie 1992"""
        
    def fl21992(self, fi, lam):
        """
        Parametry
        ----------
        współrzędne elipsoidalne punktu
        fi : szerokosć geodezyjna punktu [rad]
        lam : długosć geodezyjna punktu [rad]
        h : wysokosć punktu [m]
        
        Wynik
        -------
        współrzedne geocentryczne punktu w układzie PL-1992 [m]
        X Y 
        """
        lam0 = np.deg2rad(19)
        m0 = 0.9993
        wsp1992 = []
        for fi,lam in zip(fi,lam):
            b2 = self.a**2*(1-self.e2)    
            ep2 = (self.a**2-b2)/b2   #drugi mimosrod elipsy
            dlam = lam - lam0
            t = np.tan(fi)
            n = np.sqrt(ep2 * (np.cos(fi))**2)
            N = self.Np(fi)
            sigma = self.Sigma(fi)
                
            XGK =  sigma    +    ( ((dlam**2/2)*N*np.sin(fi)*np.cos(fi))    *    (1   +   ((dlam**2/12)*(np.cos(fi)**2)*(5 - t**2 + 9*n**2 + 4*n**4))      +         ((dlam**4/360)*(np.cos(fi)**4)*(61 - 58*t**2 + t**4 + 270*n**2 - 330*n**2*t**2))))
            YGK =  (dlam* N * np.cos(fi))  *   ( 1 +  ((dlam**2/6)   *   (np.cos(fi)**2)   *  (1 - t**2 + n**2))     +     (((dlam**4/120)*(np.cos(fi)**4)) * (5 - (18*t**2) + t**4 + (14 * n**2) - (58*n**2*t**2))))
        
            X1992 = XGK * m0 - 5300000
            Y1992 = YGK * m0 + 500000
            wsp1992.append([X1992, Y1992]) 
                
        return(wsp1992)

    """wczytywanie danych oraz funckcji z pliku """
        
    def wczytywanie(self, plik, transformacja, naglowek):
        with open(plik, 'r') as file:
            lines = file.readlines()
            lines = lines[naglowek:]
            if transformacja == 'XYZ2NEU':
                lists = {"X": [], "Y": [], "Z": [],
                         "X0": [], "Y0": [], "Z0": []}
                parts = lines[0].strip().split(',')
                lists["X0"].append(float(parts[0]))
                lists["Y0"].append(float(parts[1]))
                lists["Z0"].append(float(parts[2]))
                
                for line in lines[1:]:
                    parts = line.strip().split(',')
                    lists["X"].append(float(parts[0]))
                    lists["Y"].append(float(parts[1]))
                    lists["Z"].append(float(parts[2]))
            else:
                if transformacja == 'fl22000' or transformacja == 'fl21992':
                    lists = {"f": [], "l": []}
                    for line in lines:
                        parts = line.strip().split(',')
                        lists["f"].append(float(parts[0]))
                        lists["l"].append(float(parts[1]))
                        
                elif transformacja == 'XYZ2flh':
                    lists = {"X": [], "Y": [], "Z": []}
                    for line in lines:
                        parts = line.strip().split(',')
                        lists["X"].append(float(parts[0]))
                        lists["Y"].append(float(parts[1]))
                        lists["Z"].append(float(parts[2]))
                        
                elif transformacja == 'flh2XYZ':
                    lists = {"f": [], "l": [], "h": []}
                    for line in lines:
                        parts = line.strip().split(',')
                        lists["f"].append(float(parts[0]))
                        lists["l"].append(float(parts[1]))
                        lists["h"].append(float(parts[2]))
 
            
        if transformacja == "XYZ2flh":
            X = lists["X"]
            Y = lists["Y"]
            Z = lists["Z"]
            flh = self.XYZ2flh(X,Y,Z)
            np.savetxt(f"Wynik_{transformacja}_{args.model}.txt", flh, delimiter=";", fmt='%0.5f %0.5f %0.3f')
        elif transformacja == "flh2XYZ":
            f = lists["f"]
            l = lists["l"]
            h = lists["h"]
            xyz = self.flh2XYZ(np.deg2rad(f), np.deg2rad(l),h)
            np.savetxt(f"Wynik_{transformacja}_{args.model}.txt", xyz, delimiter=";", fmt='%0.3f %0.3f %0.3f')
        elif transformacja == "XYZ2NEU":
            X = lists["X"]
            Y = lists["Y"]
            Z = lists["Z"]
            X0 = lists["X0"]
            Y0 = lists["Y0"]
            Z0 = lists["Z0"]
            neu = self.XYZ2NEU(X,Y,Z,X0,Y0,Z0)
            np.savetxt(f"Wynik_{transformacja}_{args.model}.txt", np.vstack(neu), delimiter=";", fmt='%0.3f %0.3f %0.3f')
        elif transformacja == "fl22000":
            f = lists["f"]
            l = lists["l"]
            u2000 = self.fl22000(np.deg2rad(f), np.deg2rad(l))
            np.savetxt(f"Wynik_{transformacja}_{args.model}.txt", u2000, delimiter=";", fmt='%0.3f %0.3f')
        elif transformacja == "fl21992":
            f = lists["f"]
            l = lists["l"]
            u1992 = self.fl21992(np.deg2rad(f), np.deg2rad(l))
            np.savetxt(f"Wynik_{transformacja}_{args.model}.txt", u1992, delimiter=";", fmt='%0.3f %0.3f')
                
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-dane', type=str, help='Wpisz nazwę wraz z rozszerzeniem pliku z danymi wejsciowymi')
    parser.add_argument('-model', type=str, help='Wybierz elipsoide sposrod dostepnych: WRS84, GRS80, KRASOWSKI')
    parser.add_argument('-transformacja', type=str, help='Wybierz transformacje, z ktorej chcesz skorzystac, sposrod dostepnych: XYZ2flh, flh2XYZ, XYZ2neu, GK2000, GK1992, XYZ2NEU')
    parser.add_argument('-naglowek', type=int, help='Wpisz ile linijek nagłówka w pliku z danymi należy pominąć')
    args = parser.parse_args()
    
    elipsoidy = {'WGS84': [6378137.000, 0.00669437999014], 'GRS80': [6378137.000, 0.0066943800229], 'KRASOWSKI': [6378245.000, 0.00669342162296]}
    transf = {'XYZ2flh': 'XYZ2flh', 'flh2XYZ': 'flh2XYZ','XYZ2NEU': 'XYZ2NEU', 'fl22000': 'fl22000', 'fl21992': 'fl21992'}
    
    wybor='TAK'

    try:
        while wybor =="TAK":
            if args.model==None:
                args.model = input(str('Podaj nazwę elipsoidy: '))
            if args.dane==None:
                args.dane = input(str('Wklej scieżkę do pliku txt z danymi: '))
            if args.transformacja==None:
                args.transformacja = input(str('Podaj nazwę tranformacji, której chcesz użyć: '))
            if args.naglowek==None:
                args.naglowek = int(input('Podaj ile linijek nagłówka pliku z danymi należy pominąć: '))
                
            print('Plik z wynikami został utworzony')
            
            if args.model not in elipsoidy.keys():
                print("Nieprawidłowa nazwa elipsoidy. Wybierz spośród: WGS84, GRS80, KRASOWSKI")
            elif args.transformacja not in transf.keys():
                print("Nieprawidłowa nazwa transformacji. Wybierz spośród: XYZ2flh, flh2XYZ, XYZ2NEU, fl22000, fl21992")
            else:
                t = Transformacje(args.model)
                t.wczytywanie(args.dane, args.transformacja, args.naglowek)
                wybor = input("Czy chcesz spróbować jeszcze raz? TAK/NIE: ")
                args.model= None
                args.dane= None
                args.transformacja= None
                args.naglowek= None
    except FileNotFoundError:

        print("Plik nie został znaleziony. Upewnij się, że podałeś poprawną nazwę i ścieżkę do pliku.")
    
    finally:
       print('Dziękujemy za skorzystanie z naszego programu.')

        