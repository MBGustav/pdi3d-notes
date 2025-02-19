import SimpleITK as sitk
import numpy as np
import itkwidgets
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def images_info(list_images):
    for img in list_images:
        print( "Size(total voxels):      {}".format(img.GetSize() ))
        print( "Spacing(between voxels): {}".format(img.GetSpacing()))
        print( "Width, Height and Depth: {} x {} x {}".format(img.GetWidth(), img.GetHeight(), img.GetDepth()))
        print( "Dimension:               {}".format(img.GetDimension()))
        print("----------------------------")

        

def interpolation_method(itk_img, out_spacing=[1.0,1.0, 1.0], type='Neighbor'):
    """
    Funcao de Interpolacao de imagem:
        param:
        - img: 
        - type escolhemos os tipos[Neighbor, ...]    
    """
    #Obtemos espaco e tamanhos originais
    original_space = itk_img.GetSpacing()
    original_size = itk_img.GetSize()

    out_size = [
        int(np.ceil(original_size[0] * (original_space[0] / out_spacing[0]))),
        int(np.ceil(original_size[1] * (original_space[1] / out_spacing[1]))),
        int(np.ceil(original_size[2] * (original_space[2] / out_spacing[2])))
    ]

    resample = sitk.ResampleImageFilter()

    #espacamento e tamanho de voxels equivalentes
    resample.SetOutputSpacing(out_spacing)
    resample.SetSize(out_size)
    
    #orientacao da origem e Direcao
    resample.SetOutputDirection(itk_img.GetDirection())
    resample.SetOutputOrigin(itk_img.GetOrigin())
    #TODO: explicacao
    resample.SetTransform(sitk.Transform())
    #TODO: explicacao
    resample.SetDefaultPixelValue(itk_img.GetPixelIDValue())


    if type == 'Neighbor':
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    elif type == 'BSpline':
        resample.SetInterpolator(sitk.sitkBSpline)
    elif type == 'Linear':
        resample.SetInterpolator(sitk.sitkLinear)
    else:
        pass

    return resample.Execute(itk_img)



def myshow(img, title=None, margin=0.05, dpi=80 ):
    nda = sitk.GetArrayFromImage(img)
    spacing = img.GetSpacing()
    
    
    if nda.ndim == 3:
        # fastest dim, either component or x
        c = nda.shape[-1]
        
        # the the number of components is 3 or 4 consider it an RGB image
        if not c in (3,4):
            nda = nda[nda.shape[0]//2,:,:]
    
    elif nda.ndim == 4:
        c = nda.shape[-1]
        
        if not c in (3,4):
            raise ("Unable to show 3D-vector Image")
            exit()
            
        # take a z-slice
        nda = nda[nda.shape[0]//2,:,:,:]
            
    ysize = nda.shape[0]
    xsize = nda.shape[1]
   
    
    # Make a figure big enough to accomodate an axis of xpixels by ypixels
    # as well as the ticklabels, etc...
    figsize = (1 + margin) * ysize / dpi, (1 + margin) * xsize / dpi

    fig = plt.figure(figsize=figsize, dpi=dpi)
    # Make the axis the right size...
    ax = fig.add_axes([margin, margin, 1 - 2*margin, 1 - 2*margin])
    
    extent = (0, xsize*spacing[1], ysize*spacing[0], 0)
    
    t = ax.imshow(nda,extent=extent,interpolation=None)
    
    if nda.ndim == 2:
        t.set_cmap("gray")
    
    if(title):
        plt.title(title)


def plot_gabor_3d(kernel):
    """
    Plota um filtro de Gabor 3D.
    :param kernel: O kernel de Gabor 3D (numpy array).
    """
    # Coordenadas para plotar
    size = kernel.shape[0]
    x, y, z = np.meshgrid(
        np.arange(-size // 2 + 1, size // 2 + 1),
        np.arange(-size // 2 + 1, size // 2 + 1),
        np.arange(-size // 2 + 1, size // 2 + 1),
        indexing="ij"
    )

    # Cria uma figura 3D
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    

    # Normaliza os valores do kernel para a faixa [0, 1]
    kernel_norm = (kernel - np.min(kernel)) / (np.max(kernel) - np.min(kernel))

    # Define um limiar para exibir isosuperfícies
    threshold = 0.6  # Ajuste para visualizar diferentes níveis do filtro
    mask = kernel_norm > threshold

    # Plota os pontos do filtro onde os valores superam o limiar
    ax.scatter(x[mask], y[mask], z[mask], c=kernel_norm[mask], cmap='viridis', s=10)

    # Configurações de eixos
    ax.set_title("Filtro de Gabor 3D", fontsize=16)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.view_init(elev=20, azim=45)  # Ajusta o ângulo de visualização

    plt.show()


def myshow3d(img, xslices=[], yslices=[], zslices=[], title=None, margin=0.05, dpi=80):
    size = img.GetSize()
    img_xslices = [img[s,:,:] for s in xslices]
    img_yslices = [img[:,s,:] for s in yslices]
    img_zslices = [img[:,:,s] for s in zslices]
    
    maxlen = max(len(img_xslices), len(img_yslices), len(img_zslices))

    img_null = sitk.Image([0,0], img.GetPixelIDValue(), img.GetNumberOfComponentsPerPixel())
    img_slices = []
    d = 0
    if len(img_xslices):
        img_slices += img_xslices + [img_null]*(maxlen-len(img_xslices))
        d += 1
    if len(img_yslices):
        img_slices += img_yslices + [img_null]*(maxlen-len(img_yslices))
        d += 1
    if len(img_zslices):
        img_slices += img_zslices + [img_null]*(maxlen-len(img_zslices))
        d +=1
    if maxlen != 0:
        if img.GetNumberOfComponentsPerPixel() == 1:
            img = sitk.Tile(img_slices, [maxlen,d])
        #TODO check in code to get Tile Filter working with VectorImages
        else:
            img_comps = []
            for i in range(0,img.GetNumberOfComponentsPerPixel()):
                img_slices_c = [sitk.VectorIndexSelectionCast(s, i) for s in img_slices]
                img_comps.append(sitk.Tile(img_slices_c, [maxlen,d]))
            img = sitk.Compose(img_comps)
            
    
    myshow(img, title, margin, dpi)
