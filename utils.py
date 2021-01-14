

resolution = 0


def pix_to_mm(pix):
    mm = round(pix / resolution * 25.4, 2)
    return mm


def mm_to_pix(mm):
    pix = round(mm * resolution / 25.4)
    return pix


