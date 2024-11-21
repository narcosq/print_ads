import argparse
import os
import logging
from fpdf import FPDF
import qrcode

from db_utils import create_db_engine, select

engine = create_db_engine()

def create_pdf(data: dict, orientation: str, qr_code_path: str, output_file: str,
               title_position: tuple, qr_code_position: tuple, qr_text_position: tuple,
               text_position: tuple, long_logo_path: str, long_logo_position: tuple):
    """
    building PDF.
    """
    pdf = FPDF(orientation, 'mm', (297, 210))
    pdf.add_page()

    pdf.add_font('DejaVu', '', 'PTSans-Regular.ttf', uni=True)
    pdf.add_font('DejaVu-Bold', '', 'PTSans-Bold.ttf', uni=True)

    pdf.set_font('DejaVu-Bold', '', 70)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(*title_position)
    pdf.cell(0, 20, 'Продаю на', align='L', ln=True)
    pdf.image(long_logo_path, x=long_logo_position[0], y=long_logo_position[1], w=100)

    pdf.set_xy(*qr_text_position)
    pdf.set_font('DejaVu', '', 14)
    text = "Наведите камеру на QR-код, чтобы открыть объявление."
    formatted_text = text.replace(",", ",\n")
    pdf.multi_cell(0, 10, formatted_text, align='C')

    pdf.set_xy(*qr_code_position)
    pdf.image(qr_code_path, w=75)

    pdf.set_xy(*text_position)
    pdf.set_font('DejaVu-Bold', '', 20)
    steering_wheel_text = "Левый" if data['steering_wheel_id'] == 1 else "Правый"
    fuel_text = {
        1: "Бензин",
        2: "Дизель",
        3: "Бензин / Газ",
        5: "Гибрид",
        6: "Электро",
        7: "Газ"
    }.get(data['fuel_id'])
    gear_box_text = {
        1: "Механика",
        2: "Автомат",
        3: "Типтроник",
        4: "Вариатор",
        5: "Робот"
    }.get(data['gear_box_id'])
    transmission_text = {
        1: "Передний привод",
        2: "Задний привод",
        3: "Полный привод"
    }.get(data['transmission_id'])

    generation_name = data.get('generation_name', "")
    if generation_name:
        pdf.set_font('DejaVu-Bold', '', 35)
        pdf.set_xy(15, 50)
        pdf.multi_cell(0, 15, generation_name, align='L')

    pdf.set_font('DejaVu-Bold', '', 28)
    pdf.set_xy(20, 80)
    formatted_mileage = f"{data.get('mileage', 0):,}".replace(",", " ")
    characteristics = [
        f"• {data.get('year', '')} год",
        f"• {steering_wheel_text} руль" if steering_wheel_text else "",
        f"• {fuel_text}" if fuel_text else "",
        f"• {gear_box_text}" if gear_box_text else "",
        f"• {transmission_text}" if transmission_text else "",
        f"• {formatted_mileage} км" if data.get('mileage') else "",
        f"• {data.get('horse_power', '')} л. с." if data.get('horse_power') else ""
    ]
    pdf.multi_cell(0, 13, "\n".join(filter(None, characteristics)))


    pdf.output(output_file)

def generate_qr_code(url: str, output_file: str):
    """
    Генерирует QR-код.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=100,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    # img = img.resize((img.size[0] * 40, img.size[1] * 40))
    img.save(output_file)

def main():
    parser = argparse.ArgumentParser(description='creating PDF with QR-code.')
    parser.add_argument('--slug', type=str, required=True, help='Slug')
    parser.add_argument('--orient', choices=['P', 'L'], required=True, help='PDF orientation: P (vertical) or L (horizontal)')
    args = parser.parse_args()

    engine = create_db_engine()

    sql = f"""
    SELECT 
        car.make_id, car.model_id, car.generation_id, car.year, car.steering_wheel_id, car.fuel_id, car.body_id, 
        car.gear_box_id, car.transmission_id, car.mileage, car.horse_power, ad.slug,
        make.name AS make_name, 
        model.name AS model_name, 
        generation.name AS generation_name
    FROM ad
    LEFT JOIN car ON ad.car_id = car.id
    LEFT JOIN make ON car.make_id = make.id
    LEFT JOIN model ON car.model_id = model.id
    LEFT JOIN generation ON car.generation_id = generation.id
    WHERE ad.slug = "{args.slug}";
    """

    data = select(sql, engine).to_dict(orient='records')
    if not data:
        logging.error(f"Нет данных для объявления с slug {args.slug}")
        return
    data = data[0]

    qr_code_path = 'qr_code.png'
    url = f"https://www.mashina.kg/details/{data['slug']}"
    generate_qr_code(url, qr_code_path)

    output_file = f"{args.slug}.pdf"
    long_logo_path = 'logo.png'


    title_position = (15, 15)
    qr_code_position = (182, 110)
    qr_text_position = (152, 90)
    text_position = (10, 30)
    long_logo_position = (150, 15)



    create_pdf(data, args.orient, qr_code_path, output_file,
               title_position, qr_code_position, qr_text_position, text_position, long_logo_path, long_logo_position)
    os.remove(qr_code_path)

    print(f"PDF файл создан: {output_file}")

if __name__ == '__main__':
    main()
