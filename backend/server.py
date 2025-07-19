UPLOAD = os.path.join(BASE, 'uploads')
SPLIT = os.path.join(BASE, 'split_letters_output')



from flask import send_from_directory, render_template_string, redirect

@app.route('/view_letters')
def view_letters():
    image_folder = SPLIT
    image_files = sorted([
        f for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])

    images_html = ''
    for filename in image_files:
        images_html += f'''
            <div style="display:inline-block; margin:10px; text-align:center;">
                <img src="/get_letter/{filename}" style="height:100px; display:block; margin-bottom:5px;" />
                <a href="/get_letter/{filename}" download="{filename}">{filename}</a>
            </div>
        '''

    return render_template_string(f'''
        <html dir="rtl" lang="he">
        <head><title>תצוגת האותיות החתוכות</title></head>
        <body style="font-family:Arial; text-align:center; background:#fafafa; padding:30px;">
            <h2>✅ האותיות שנחתכו:</h2>
            {images_html}
        </body>
        </html>
    ''')

@app.route('/get_letter/<filename>')
def get_letter(filename):
    return send_from_directory(SPLIT, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

