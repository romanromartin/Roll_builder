import os
import sqlite3
import sys

import utils
from PIL import Image
from PIL import ImageCms, ImageDraw, TiffTags, TiffImagePlugin

conn = sqlite3.connect("test_database.db")
cursor = conn.cursor()


class Roll:
    def __init__(self):
        self.id_ = 0
        self.resolution = 0
        self.maxWidth_unit = 0
        self.fin_min_size = 100000000000000
        self.print_square = 0
        self.total_width = 0
        self.eff_str = ''

    def clear_DB(self):
        # --- making DB of pieces
        cursor.execute("DROP TABLE IF EXISTS remainders ")
        cursor.execute("CREATE TABLE IF NOT EXISTS remainders (id, basket, width, height, status, rem_x, rem_y) ")
        cursor.execute(" UPDATE units SET rotate = 'False', done = 'uncuted', pos_x = 0, pos_y = 0 ")

    def read_files(self, dir_print, openFolder):
        cursor.execute("DROP TABLE IF EXISTS units ")
        cursor.execute("CREATE TABLE IF NOT EXISTS units "
                       "(id, name, width, height, resolution, done, pos_x, pos_y, rotate, basket) ")
        self.id_ = 0
        for file in dir_print:
            ext = file.rsplit('.', 1)[-1]
            if ext != 'tif' or not os.path.isfile(openFolder + file):
                continue
            im = Image.open(openFolder + file)
            utils.resolution = self.resolution = im.info.get('dpi')[0]
            if im.mode != 'CMYK':
                print('O-o-o No! RGB!', file)
                sys.exit()
            width = utils.pix_to_mm(im.size[0])
            height = utils.pix_to_mm(im.size[1])
            execute = (self.id_, file, width, height, self.resolution, 'uncuted', 0, 0, 'False', '')
            cursor.execute("INSERT INTO units VALUES (?,?,?,?,?,?,?,?,?,?)", execute)
            conn.commit()
            self.id_ += 1
        # Checking
        # is there at least one file in the folder in the format "TIF"
        if self.id_ < 1:
            print(" There is no layouts 'tif' in folder 'oracal'")

        # comparison resolution of layouts
        arr_res = []
        for res in range(self.id_):
            check_resolution = cursor.execute(" SELECT resolution FROM units WHERE id = " + str(res)).fetchone()[0]
            if check_resolution not in arr_res:
                arr_res.append(check_resolution)
        if len(arr_res) > 1:
            while True:
                try:
                    inp_resolution = int(input(
                        'Layouts have a different resolutions' + str(arr_res) + '\n' + 'Choose resolution from list'))
                except ValueError:
                    print("Error! This is not a number, try agan.")
                else:
                    if inp_resolution in arr_res:
                        print(inp_resolution)
                        break
                    else:
                        print('There is no such resolution in the list')
            utils.resolution = self.resolution = inp_resolution
            change_resolution = cursor.execute(
                " SELECT name FROM units WHERE resolution != " + str(inp_resolution)).fetchall()
            for ch_layout_name in change_resolution:
                layout_ = Image.open(openFolder + ch_layout_name[0])
                # print(layout_.info.get('dpi')[0])
                size1 = round(round(layout_.size[0] / layout_.info.get('dpi')[0] * 25.4, 2) * self.resolution / 25.4)
                size2 = round(round(layout_.size[1] / layout_.info.get('dpi')[0] * 25.4, 2) * self.resolution / 25.4)
                layout_ = layout_.resize((size1, size2), 3)
                layout_.save(openFolder + ch_layout_name[0], dpi=(self.resolution, self.resolution))
                query_change_res = (" UPDATE units SET resolution = " + str(inp_resolution) +
                                    " WHERE name = '" + str(ch_layout_name[0])) + "'"
                # print(query_change_res)
                cursor.execute(query_change_res)
            conn.commit()

    def min_width_piece(self):
        # ------------MIN WIDTH ROLL & MIN SIZE PIECE---------------
        self.print_square = 0
        for m in range(self.id_):
            check_width_roll = cursor.execute(" SELECT width, height FROM units WHERE id = " + str(m)).fetchone()
            self.print_square += check_width_roll[0] * check_width_roll[1] / 1000000
            if check_width_roll[0] >= check_width_roll[1]:
                roll = check_width_roll[1]
                min_size = check_width_roll[1]
            else:
                roll = check_width_roll[0]
                min_size = check_width_roll[0]
            if roll >= self.maxWidth_unit:
                self.maxWidth_unit = roll
            if min_size < self.fin_min_size:
                self.fin_min_size = min_size
            m += 1
        # print('MAX width of layouts', self.maxWidth_unit)

    # Add leftovers function
    def add_remainder(self, id_r, basket_r, width_r, height_r, pos_x_r, pos_y_r):
        if width_r < self.fin_min_size or height_r < self.fin_min_size:
            status = 'small'
        else:
            status = 'in progress'
        executeRem = [id_r, basket_r, width_r, height_r, status, pos_x_r, pos_y_r]
        cursor.execute("INSERT INTO remainders VALUES (?,?,?,?,?,?,?)", executeRem)
        id_r += 1
        return id_r

    def roll_constructor(self, width_roll_selected, openFolder):
        basket = 0
        id_rem = 0
        width_pos = 0
        self.total_width = 0
        for n in range(self.id_):
            sorted_id_width = \
                cursor.execute(" SELECT id FROM units WHERE done = 'uncuted' ORDER BY width DESC LIMIT 1").fetchone()[0]
            sorted_max_width = cursor.execute(" SELECT width FROM units WHERE id = " + str(sorted_id_width)).fetchone()[
                0]
            # print(sorted_id_width, sorted_max_width)
            sorted_id_height = \
                cursor.execute(" SELECT id FROM units WHERE done = 'uncuted' ORDER BY height DESC LIMIT 1").fetchone()[
                    0]
            sorted_max_height = cursor.execute(
                " SELECT height FROM units WHERE id = " + str(sorted_id_height)).fetchone()[0]
            if sorted_max_width >= sorted_max_height:
                query = " UPDATE units SET done = 'done' WHERE id = " + str(sorted_id_width)
                id_piece = sorted_id_width
                to_rotate = False
            else:
                query = " UPDATE units SET done = 'done' WHERE id = " + str(sorted_id_height)
                to_rotate = True
                id_piece = sorted_id_height
            cursor.execute(query)
            in_progress_file = cursor.execute(" SELECT name FROM units WHERE id = " + str(id_piece)).fetchone()
            in_progress = Image.open(openFolder + in_progress_file[0])
            width = utils.pix_to_mm(in_progress.size[0])
            height = utils.pix_to_mm(in_progress.size[1])

            # Finding a suitable piece in the leftovers
            rem_size = cursor.execute(
                " SELECT id, width, height, status, rem_x, rem_y, basket FROM remainders ORDER BY basket").fetchall()
            piece_to_rem = False
            for rem_ in rem_size:
                if rem_[3] == 'in progress':
                    if width <= rem_[2] and height <= rem_[1]:
                        piece_to_rem = True
                        query_posXY_rem = (" UPDATE units SET pos_x = " + str(rem_[4]) + ", pos_y = " + str(rem_[5])
                                           + ", rotate = 'True' "
                                           + ", basket = " + str(rem_[6])
                                           + " WHERE id = " + str(id_piece))
                        cursor.execute(query_posXY_rem)
                        cursor.execute(" UPDATE remainders SET status = 'done' WHERE id = " + str(rem_[0]))
                        # Adding two leftovers after placing a matching piece
                        id_rem = self.add_remainder(id_rem, rem_[6], height, round(rem_[2] - width, 2),
                                                    rem_[4], rem_[5] + utils.mm_to_pix(width))
                        id_rem = self.add_remainder(
                            id_rem, rem_[6], round(rem_[1] - height, 2),
                            rem_[2], rem_[4] + utils.mm_to_pix(height), rem_[5])
                        break
                    elif width <= rem_[1] and height <= rem_[2]:
                        piece_to_rem = True
                        query_posXY_rem = (" UPDATE units SET pos_x = " + str(rem_[4])
                                           + ", pos_y = " + str(rem_[5])
                                           + ", basket = " + str(rem_[6])
                                           + " WHERE id = " + str(id_piece))
                        cursor.execute(query_posXY_rem)
                        cursor.execute(" UPDATE remainders SET status = 'done' WHERE id = " + str(rem_[0]))
                        # Adding two leftovers after placing a matching piece
                        id_rem = self.add_remainder(id_rem, rem_[6], width, round(rem_[2] - height, 2),
                                                    rem_[4], rem_[5] + utils.mm_to_pix(height))
                        id_rem = self.add_remainder(id_rem, rem_[6], round(rem_[1] - width, 2), rem_[2],
                                                    rem_[4] + utils.mm_to_pix(width), rem_[5])
                        break

            # If there is no suitable size in the leftovers, a new basket is created and the first item is added
            if not piece_to_rem:
                cursor.execute(" UPDATE units SET   basket = " + str(basket) + " WHERE id = " + str(id_piece))
                if to_rotate:
                    self.total_width += in_progress.height
                    cursor.execute(" UPDATE units SET rotate = 'True' WHERE id = " + str(sorted_id_height))
                else:
                    self.total_width += in_progress.width
                query_pos_x = " UPDATE units SET pos_x = " + str(width_pos) + " WHERE id = " + str(id_piece)
                cursor.execute(query_pos_x)

                #  Position of remainder
                if to_rotate:
                    remainder = (
                        in_progress.height, utils.mm_to_pix(width_roll_selected)
                        - in_progress.width, width_pos, in_progress.width)
                    width_pos += in_progress.height
                else:
                    remainder = (
                        in_progress.width, utils.mm_to_pix(width_roll_selected)
                        - in_progress.height, width_pos, in_progress.height)
                    width_pos += in_progress.width

                # Adding reminders to a database
                if utils.mm_to_pix(self.fin_min_size) < remainder[0] \
                        or utils.mm_to_pix(self.fin_min_size) < remainder[1]:
                    execute_rem = (id_rem, basket, utils.pix_to_mm(remainder[0]),
                                   utils.pix_to_mm(remainder[1]), 'in progress', remainder[2], remainder[3])
                else:
                    # Checking remainder by min size
                    execute_rem = (id_rem, basket, utils.pix_to_mm(remainder[0]),
                                   utils.pix_to_mm(remainder[1]), 'small', remainder[2], remainder[3])
                cursor.execute("INSERT INTO remainders VALUES (?,?,?,?,?,?,?)", execute_rem)
                id_rem += 1
                basket += 1
            conn.commit()

            n += 1

        # This block rotate basket when height of basket less width and width less roll
        m = 0
        shift = 0
        while m < basket:
            check_to_rotate = cursor.execute(" SELECT id, width, height, pos_x, pos_y, rotate FROM units "
                                             "WHERE basket = " + str(m)).fetchall()
            base_ = cursor.execute("SELECT width, height, rotate, pos_x FROM units WHERE basket = " + str(m) +
                                   " AND pos_y = 0").fetchone()
            if base_[2] == 'False':
                x = utils.mm_to_pix(base_[0])
            else:
                x = utils.mm_to_pix(base_[1])
            y = 0
            for b_ in check_to_rotate:
                if b_[5] == 'False':
                    h = utils.mm_to_pix(b_[2])
                else:
                    h = utils.mm_to_pix(b_[1])
                if y < b_[4] + h:
                    y = b_[4] + h
            if utils.mm_to_pix(width_roll_selected) > x > y:
                basket_to_rotate = cursor.execute(
                    " SELECT id, pos_x, pos_y, rotate FROM units WHERE basket = " + str(m)).fetchall()
                for unit_to_rotate in basket_to_rotate:
                    if unit_to_rotate[3] == 'True':
                        cursor.execute(" UPDATE units SET rotate = 'False' WHERE id = " + str(unit_to_rotate[0]))
                    elif unit_to_rotate[3] == 'False':
                        cursor.execute(" UPDATE units SET rotate = 'True' WHERE id = " + str(unit_to_rotate[0]))
                    new_pos_X = base_[3] + unit_to_rotate[2] - shift
                    new_pos_Y = unit_to_rotate[1] - base_[3]
                    cursor.execute(" UPDATE units SET pos_x = " + str(new_pos_X)
                                   + ", pos_y = " + str(new_pos_Y)
                                   + " WHERE id = " + str(unit_to_rotate[0]))
                self.total_width = self.total_width - x + y
                shift_basket = x - y
            else:
                basket_to_shift = cursor.execute(
                    " SELECT id, pos_x, pos_y, rotate FROM units WHERE basket = " + str(m)).fetchall()
                for unit_to_shift in basket_to_shift:
                    new_pos_X = unit_to_shift[1] - shift
                    cursor.execute(" UPDATE units SET pos_x = " + str(new_pos_X)
                                   + " WHERE id = " + str(unit_to_shift[0]))
                shift_basket = 0
            conn.commit()
            shift += shift_basket
            m += 1

    # Function for calculating efficiency and areas
    def count_efficiency(self, width_roll_selected):
        self.eff_str = ''
        efficiency_small = cursor.execute(" SELECT width, height FROM remainders WHERE status = 'small'").fetchall()
        efficiency_inProgress = cursor.execute(
            " SELECT width, height FROM remainders WHERE status = 'in progress'").fetchall()
        totalEffSmall = 0
        totalEffInprogress = 0
        for eff in efficiency_small:
            totalEffSmall += eff[0] * eff[1] / 1000000
        self.eff_str += 'Small leftovers ' + str(round(totalEffSmall, 2)) + '\n'
        # print('Small leftovers ', round(totalEffSmall, 2))
        for eff in efficiency_inProgress:
            totalEffInprogress += eff[0] * eff[1] / 1000000
        self.eff_str += 'Big leftovers ' + str(round(totalEffInprogress, 2)) + '\n'
        # print('Big leftovers', round(totalEffInprogress, 2))
        total_square = width_roll_selected * utils.pix_to_mm(self.total_width) / 1000000
        self.eff_str += 'Printing area ' + str(round(total_square, 2)) + '\n' \
                        + 'Layouts area ' + str(round(self.print_square, 2)) + '\n'
        # print('Printing area', round(total_square, 2))
        # print('Layouts area', round(self.print_square, 2))
        efficiency = round(self.print_square, 2) / (round(total_square, 2) / 100)
        self.eff_str += 'Efficiency ' + str(round(efficiency)) + '%\n'
        # print('Efficiency', round(efficiency), '%')

    def layout_builder(self, w_roll, openFolder):
        # Building and saving the roll layout
        layout = Image.new('CMYK', (self.total_width, utils.mm_to_pix(w_roll)))  # !!!!!!!!!!!!!
        for paste_id in range(self.id_):
            paste_query = cursor.execute("SELECT name, pos_x, pos_y, rotate FROM units WHERE id = "
                                         + str(paste_id)).fetchone()
            paste_file = Image.open(openFolder + paste_query[0])
            if paste_query[3] == 'True':
                paste_file = paste_file.transpose(Image.ROTATE_90)
            paste_file_frame = ImageDraw.Draw(paste_file)
            paste_file_frame.line([(0, 0),
                                   (paste_file.size[0] - 1, 0),
                                   (paste_file.size[0] - 1, paste_file.size[1] - 1),
                                   (0, paste_file.size[1] - 1),
                                   (0, 0)], fill=(80, 80, 80, 80), width=1)
            layout.paste(paste_file, (paste_query[1], paste_query[2]))
        os.mkdir(openFolder + 'out/')
        layout.save(openFolder + 'out/out.tif', dpi=(self.resolution, self.resolution))
