'''
GOAL:
- for some input galaxy sample, gather their corresponding .fits cutouts and calculate their SNR using photutils.aperture.CircularAperture. Do so for 15" and 30" apertures.
Steps:
---create empty lists, first set with S/N values and second set with flags indicating whether the values > 10
---for each galaxy, isolate VFID and navigate to the directory hosting the cutouts. Grab the signal and noise images
---define central x,y coordinates of image; approximate as center of galaxy
---from header information, extract the number of arcsec per pixel
---convert 15, 30 arcseconds to pixels (unique to each cutout)
---do the aperture thingy
---append columns to gal_sample table
---if save == True, then add each column as a .txt in homedir
'''

import glob
import sys
import os
homedir = os.getenv("HOME")

import numpy as np
from matplotlib import pyplot as plt
from astropy.io import fits
from astropy.table import Table
from photutils.aperture import CircularAperture
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import skycoord_to_pixel

#os.chdir(homedir+'/github/wisesize/SNR')
#from find_groups import

def surface_brightness(galaxy_table,column_name,im_path,im_name):
    surf15 = np.zeros(len(galaxy_table),dtype=float)
    surf30 = np.zeros(len(galaxy_table),dtype=float)
    try:
        objnames = galaxy_table['group_name']
    except:
        print('group_name column not found. appending relevant group columns to galaxy table.')
        #INSERT FIND_GROUPS CODE HERE TO GENERATE THE APPROPRIATE TABLE!
        #THIS WILL CREATE THE GENERIC GROUP_NAME COLUMN IF IT DOES NOT EXIST.
        #...AND AN NCOMP COLUMN. AND A GROUP FLAG. AND A PRIMARY GROUP FLAG. ETC.
    for n in galaxy_table:
        print(f'{homedir}/{im_path}{n['group_name']}*{im_name}')
        print(n['VFID'],n['objname'])
        im = glob.glob(f'{homedir}/{im_path}{n['group_name']}*{im_name}')[0]
        #open the images...
        hdu_im=fits.open(im)[0]   
        #WCS header information
        wcs_w3 = WCS(hdu_im) 
        img_len = len(hdu_im.data)
        #if single galaxy, then its position lies in the center of the image
        if n['ncomp']==1:
            position = (int(img_len/2.),int(img_len/2.))   #(x,y) pixel coords
        #if a group galaxy, then use projected group cutout and galaxy's RA, DEC to find SNR
        else:
            RA = n['RA']
            DEC = n['DEC']   
            coor = SkyCoord(RA, DEC, unit="deg")
            #extract x and y coordinates of each group galaxy
            xy = skycoord_to_pixel(coor, wcs_w3)
            position = (xy[0],xy[1])
        len_arcsec = np.abs(hdu_im.header['NAXIS1']*hdu_im.header['CD1_1'])*3600.
        arcsec_per_pixel = len_arcsec/hdu_im.header['NAXIS1']     #should be 2.75"/px for W1, W3
        #15" and 30" apertures
        radius_15 = 15/arcsec_per_pixel
        radius_30 = radius_15*2
        #note --> the masks act as 'cookie cutters,' isolating the image region within the given radius
        aper15 = CircularAperture(position,radius_15)
        mask15 = aper15.to_mask(method='center')   #'cookie cutter'
        aper30 = CircularAperture(position,radius_30)
        mask30 = aper30.to_mask(method='center')
        data15_im = mask15.multiply(hdu_im.data)
        data30_im = mask30.multiply(hdu_im.data)
        data15_im = data15_im[data15_im!=0.]
        data30_im = data30_im[data30_im!=0.]
        signal15 = np.sqrt(np.sum(data15_im**2))
        signal30 = np.sqrt(np.sum(data30_im**2))
        surf15[galaxy_table['group_name']==n['group_name']] = round(signal15,1)
        surf30[galaxy_table['group_name']==n['group_name']] = round(signal30,1)
    return surf15, surf30
    

def snr(galaxy_table,column_name,im_path,im_name,std_name,output_name):
    
    snr15 = np.zeros(len(galaxy_table),dtype=float)
    snr30 = np.zeros(len(galaxy_table),dtype=float)
    
    snr15_flag = np.zeros(len(galaxy_table),dtype=bool)
    snr30_flag = np.zeros(len(galaxy_table),dtype=bool)

    try:
        objnames = galaxy_table['group_name']
    except:
        print('group_name column not found. appending relevant group columns to galaxy table.')
        #INSERT FIND_GROUPS CODE HERE TO GENERATE THE APPROPRIATE TABLE!
        #THIS WILL CREATE THE GENERIC GROUP_NAME COLUMN IF IT DOES NOT EXIST.
        #...AND AN NCOMP COLUMN. AND A GROUP FLAG. AND A PRIMARY GROUP FLAG. ETC.

####### Can't create the find_groups.py code until I know where the group-related data will be stored #######
    
    for n in galaxy_table:
        im = glob.glob(f'{im_path}{n['group_name']}*{im_name}')[0]
        std = glob.glob(f'{im_path}{n['group_name']}*{std_name}')[0]

        #open the images...
        hdu_im=fits.open(im)[0]
        hdu_std=fits.open(std)[0]
          
        #WCS header information
        wcs_w3 = WCS(hdu_im)
        
        img_len = len(hdu_im.data)

        #if single galaxy, then its position lies in the center of the image
        if n['ncomp']==1:
            position = (int(img_len/2.),int(img_len/2.))   #(x,y) pixel coords

        #if a group galaxy, then use projected group cutout and galaxy's RA, DEC to find SNR
        else:
            RA = n['RA']
            DEC = n['DEC']
            
            coor = SkyCoord(RA, DEC, unit="deg")
            #extract x and y coordinates of each group galaxy
            xy = skycoord_to_pixel(coor, wcs_w3)
            position = (xy[0],xy[1])
        
        len_arcsec = np.abs(hdu_im.header['NAXIS1']*hdu_im.header['CD1_1'])*3600.
        arcsec_per_pixel = len_arcsec/hdu_im.header['NAXIS1']     #should be 2.75"/px for W1, W3

        #15" and 30" apertures
        radius_15 = 15/arcsec_per_pixel
        radius_30 = radius_15*2

        #note --> the masks act as 'cookie cutters,' isolating the image region within the given radius
        aper15 = CircularAperture(position,radius_15)
        mask15 = aper15.to_mask(method='center')   #'cookie cutter'
        aper30 = CircularAperture(position,radius_30)
        mask30 = aper30.to_mask(method='center')

        data15_im = mask15.multiply(hdu_im.data)
        data15_std = mask15.multiply(hdu_std.data)
        data30_im = mask30.multiply(hdu_im.data)
        data30_std = mask30.multiply(hdu_std.data)

        data15_im = data15_im[data15_im!=0]
        data15_std = data15_std[data15_std!=0]
        data30_im = data30_im[data30_im!=0]
        data30_std = data30_std[data30_std!=0]

        noise15 = np.sqrt(np.sum(data15_std**2))
        noise30 = np.sqrt(np.sum(data30_std**2))
        signal15 = np.sqrt(np.sum(data15_im**2))
        signal30 = np.sqrt(np.sum(data30_im**2))

        num15 = signal15/noise15
        snr15[galaxy_table['group_name']==n['group_name']] = round(num15,1)
        num30 = signal30/noise30
        snr30[galaxy_table['group_name']==n['group_name']] = round(num30,1)
        
        if (snr15 > 10.) & (str(snr15) != 'inf'):
            snr15_flag[galaxy_table['group_name']==n['group_name']] = True            
        if (snr15 < 10.) & (str(snr15) != 'inf'):
            snr15_flag[galaxy_table['group_name']==n['group_name']] = False
        if str(snr15) == 'inf':
            snr15_flag[galaxy_table['group_name']==n['group_name']] = False
        
        if (snr30 > 10.) & (str(snr30) != 'inf'):
            print(vfid, 'snr30 > 10')
            snr30_flag[galaxy_table['group_name']==n['group_name']] = True
        if (snr30 < 10.) & (str(snr30) != 'inf'):
            snr30_flag[galaxy_table['group_name']==n['group_name']] = False
        if str(snr30) == 'inf':
            snr30_flag[galaxy_table['group_name']==n['group_name']] = False

    count15 = 0
    count30 = 0
    count_both = 0
    print(len(snr15_flag),len(snr30_flag))
    for i in range(len(galaxy_table)):
        if snr15_flag[i] == 1:
            count15 += 1
        if snr30_flag[i] == 1:
            count30 += 1
        if (snr15_flag[i] == 1) & (snr30_flag[i] == 1):
            count_both += 1
    print('SNR>10 for 15arc: ',count15,'of ',len(snr15_flag))
    print('SNR>10 for 30arc: ',count30,'of ',len(snr15_flag))
    print('# galaxies with SNR>10 for both: ',count_both)

    galaxy_table.add_columns([snr15, snr15_flag, snr30, snr30_flag],
                             names=['SNR15','SNR15_flag','SNR30','SNR30_flag'])
    Table.write(galaxy_table,overwrite=True)
    print()
    print(f'Columns added to {galaxy_table}')
    
if __name__ == '__main__':
    
    if '-h' in sys.argv or '--help' in sys.argv:
        print("Usage: %s [-param_file (name of parameter file, no single or double quotation marks)] [-run_all (True or False; run on all galaxies)]")
        sys.exit(1)
    
    if '-param_file' in sys.argv:
        p = sys.argv.index('-param_file')
        param_file = str(sys.argv[p+1])

    if '-run_all' in sys.argv:
        run_all = True
           
    #create dictionary with keywords and values, from parameter .txt file

    param_dict = {}
    with open(param_file) as f:
        for line in f:
            try:
                key = line.split()[0]
                val = line.split()[1]
                param_dict[key] = val
            except:
                continue    
    
    galaxy_table = Table.read(homedir+'/'+param_dict['catalog'])
    column_name = param_dict['column_name']
    im_path = param_dict['im_path']
    im_name = param_dict['im_name']
    std_name = param_dict['std_name']
    output_name = param_dict['output_name']
    
    if run_all:
        surface_brightness(galaxy_table,column_name,im_path,im_name)
        #snr(galaxy_table,column_name,im_path,im_name,std_name,output_name)

















