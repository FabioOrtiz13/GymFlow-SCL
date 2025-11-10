"""
Servicio para integrar con ExerciseDB API
API: https://github.com/ExerciseDB/exercisedb-api
Endpoint: https://exercisedb.dev/api/v2/
"""
import requests
from django.core.cache import cache

# Diccionario de traducciones (ordenado por longitud para mejor matching)
TRADUCCIONES = {
    # Partes del cuerpo (MUY IMPORTANTE para filtros)
    'chest': 'Pecho',
    'back': 'Espalda', 
    'shoulders': 'Hombros',
    'upper arms': 'Brazos',
    'lower arms': 'Antebrazos',
    'upper legs': 'Piernas',
    'lower legs': 'Pantorrillas',
    'waist': 'Core',  # Waist se traduce como Core para que coincida con filtro
    'cardio': 'Cardio',
    'neck': 'Cuello',
    
    # Ejercicios compuestos (primero los más largos)
    'barbell bench press': 'Press de Banca con Barra',
    'dumbbell bench press': 'Press de Banca con Mancuernas',
    'incline bench press': 'Press Inclinado',
    'decline bench press': 'Press Declinado',
    'bench press': 'Press de Banca',
    
    'barbell squat': 'Sentadilla con Barra',
    'front squat': 'Sentadilla Frontal',
    'goblet squat': 'Sentadilla Goblet',
    'jump squat': 'Sentadilla con Salto',
    'bulgarian split squat': 'Sentadilla Búlgara',
    'squat': 'Sentadilla',
    
    'romanian deadlift': 'Peso Muerto Rumano',
    'sumo deadlift': 'Peso Muerto Sumo',
    'deadlift': 'Peso Muerto',
    
    'shoulder press': 'Press Militar',
    'military press': 'Press Militar',
    'overhead press': 'Press sobre Cabeza',
    'arnold press': 'Press Arnold',
    
    'barbell row': 'Remo con Barra',
    'dumbbell row': 'Remo con Mancuerna',
    'cable row': 'Remo en Polea',
    'seated row': 'Remo Sentado',
    
    # Ejercicios simples
    'pull-up': 'Dominadas',
    'pull up': 'Dominadas',
    'chin-up': 'Dominadas Supinas',
    'chin up': 'Dominadas Supinas',
    'leg press': 'Prensa de Piernas',
    'leg curl': 'Curl Femoral',
    'leg extension': 'Extensión de Piernas',
    'calf raise': 'Elevación de Gemelos',
    'lunge': 'Zancada',
    'lunges': 'Zancadas',
    
    'bicep curl': 'Curl de Bíceps',
    'hammer curl': 'Curl Martillo',
    'preacher curl': 'Curl Predicador',
    'concentration curl': 'Curl Concentrado',
    
    'tricep extension': 'Extensión de Tríceps',
    'tricep dips': 'Fondos de Tríceps',
    'close grip bench press': 'Press con Agarre Cerrado',
    'tricep pushdown': 'Extensión en Polea',
    
    'plank': 'Plancha',
    'side plank': 'Plancha Lateral',
    'crunch': 'Abdominales',
    'crunches': 'Abdominales',
    'sit-up': 'Abdominales',
    'sit up': 'Abdominales',
    'russian twist': 'Giros Rusos',
    'leg raise': 'Elevación de Piernas',
    'mountain climber': 'Escaladores',
    'bicycle crunch': 'Abdominales Bicicleta',
    
    'push-up': 'Flexiones',
    'push up': 'Flexiones',
    'burpee': 'Burpees',
    'dip': 'Fondos',
    'dips': 'Fondos',
    'lateral raise': 'Elevación Lateral',
    'front raise': 'Elevación Frontal',
    'face pull': 'Face Pull',
    'shrug': 'Encogimientos',
    
    # Equipamiento
    'barbell': 'Barra',
    'dumbbell': 'Mancuernas',
    'kettlebell': 'Pesa Rusa',
    'body weight': 'Peso Corporal',
    'cable': 'Polea',
    'machine': 'Máquina',
    'resistance band': 'Banda',
    'medicine ball': 'Balón Medicinal',
}

def traducir_texto(texto):
    """Traduce texto de inglés a español usando diccionario"""
    if not texto or texto == 'N/A':
        return texto
    
    texto_original = texto
    texto_lower = texto.lower().strip()
    
    # Primero buscar coincidencias exactas
    if texto_lower in TRADUCCIONES:
        return TRADUCCIONES[texto_lower]
    
    # Luego buscar coincidencias parciales (más largas primero)
    items_ordenados = sorted(TRADUCCIONES.items(), key=lambda x: len(x[0]), reverse=True)
    for ingles, espanol in items_ordenados:
        if ingles in texto_lower:
            # Reemplazar todas las variantes
            texto = texto.lower().replace(ingles, espanol)
            texto = texto.replace(ingles.title(), espanol)
            texto = texto.replace(ingles.upper(), espanol.upper())
    
    # Capitalizar primera letra
    if texto != texto_original and texto:
        texto = texto[0].upper() + texto[1:] if len(texto) > 1 else texto.upper()
    
    return texto


class ExerciseDBService:
    """Servicio para consumir ExerciseDB API"""
    # API pública de ExerciseDB V1 (Open Source - NO requiere API key)
    BASE_URL_V1 = "https://exercisedb.dev/api/v1"
    
    # Para V2 (más completa) necesitas API key de RapidAPI
    BASE_URL_V2 = "https://exercisedb-api1.p.rapidapi.com"
    API_KEY = "0926b553a3msh944a16b9f872cd4p161c55jsn6ae16e058887"
    
    # Modo de operación
    USE_FALLBACK_ONLY = True  # Usar SOLO ejercicios de respaldo (42 ejercicios)
    USE_V1 = True  # Usar V1 si se necesita API
    
    @staticmethod
    def get_fallback_exercises():
        """Ejercicios de respaldo organizados por zona muscular"""
        return [
            # ========== PECHO ==========
            {
                'id': 'bench-press',
                'name': 'Press de Banca',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/03/barbell-bench-press-benefits-1024x683.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif',
                'equipments': 'Barra',
                'bodyParts': 'Pecho',
                'targetMuscles': 'Pectorales',
                'secondaryMuscles': 'Tríceps, Deltoides',
                'overview': 'Ejercicio fundamental para desarrollo del pecho. Fortalece pectorales, deltoides anterior y tríceps.',
                'instructions': ['Acostarse en el banco con los pies en el suelo', 'Agarrar la barra con manos más anchas que los hombros', 'Bajar la barra controladamente al pecho', 'Empujar hacia arriba hasta extender los brazos'],
                'tips': ['Mantén los pies firmes en el suelo', 'No arquees excesivamente la espalda', 'La barra debe tocar el pecho', 'Empuja con fuerza explosiva'],
                'variations': ['Incline Bench Press', 'Decline Bench Press', 'Dumbbell Bench Press'],
            },
            {
                'id': 'barbell-squat',
                'name': 'Sentadillas con Barra',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2023/05/barbell-squat.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Squat.gif',
                'equipments': 'Barra',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Cuádriceps',
                'secondaryMuscles': 'Glúteos, Femorales',
                'overview': 'El rey de los ejercicios para piernas. Desarrolla fuerza y masa muscular en todo el tren inferior.',
                'instructions': ['Coloca la barra en la parte alta de los trapecios', 'Pies al ancho de hombros, dedos ligeramente hacia afuera', 'Bajar flexionando rodillas y cadera hasta muslos paralelos al suelo', 'Subir con fuerza empujando desde los talones'],
                'tips': ['Rodillas siempre en línea con los pies', 'Mantén el core activo y la espalda recta', 'Mira al frente, no hacia abajo', 'Desciende controladamente'],
                'variations': ['Front Squat', 'Bulgarian Split Squat', 'Goblet Squat'],
            },
            {
                'id': 'deadlift',
                'name': 'Peso Muerto',
                'imageUrl': 'https://www.muscleandfitness.com/wp-content/uploads/2013/07/deadlift.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Deadlift.gif',
                'equipments': 'Barra',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Espalda Baja, Lumbares',
                'secondaryMuscles': 'Femorales, Glúteos, Trapecios',
                'overview': 'Ejercicio compuesto fundamental. Desarrolla fuerza en espalda, piernas y todo el posterior.',
                'instructions': ['Barra en el suelo frente a ti', 'Pies al ancho de caderas, debajo de la barra', 'Agarrar la barra con manos fuera de las rodillas', 'Espalda recta, pecho hacia afuera', 'Levantar extendiendo cadera y rodillas simultáneamente'],
                'tips': ['NUNCA redondees la espalda', 'Mantén la barra pegada al cuerpo', 'Empuja con los talones', 'Finaliza con cadera extendida y hombros atrás'],
                'variations': ['Romanian Deadlift', 'Sumo Deadlift', 'Trap Bar Deadlift'],
            },
            {
                'id': 'pull-up',
                'name': 'Dominadas',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/10/wide-grip-pull-up.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Pull-up.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Dorsales',
                'secondaryMuscles': 'Bíceps, Deltoides Posterior, Romboides',
                'overview': 'Ejercicio de tracción vertical excelente para desarrollar la espalda. Uno de los mejores ejercicios con peso corporal.',
                'instructions': ['Colgar de la barra con brazos extendidos', 'Agarre pronación (palmas alejadas) más ancho que hombros', 'Subir tirando con la espalda hasta que la barbilla pase la barra', 'Bajar controladamente hasta brazos extendidos'],
                'tips': ['Evita balancearte o usar impulso', 'Contrae las escápulas al subir', 'Piensa en llevar los codos hacia abajo', 'Extensión completa en cada repetición'],
                'variations': ['Chin-ups (agarre supino)', 'Neutral Grip Pull-ups', 'Assisted Pull-ups'],
            },
            {
                'id': 'shoulder-press',
                'name': 'Press Militar',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2021/08/barbell-shoulder-press.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Standing-Military-Press.gif',
                'equipments': 'Barra',
                'bodyParts': 'Hombros',
                'targetMuscles': 'Deltoides',
                'secondaryMuscles': 'Tríceps, Core, Trapecio Superior',
                'overview': 'Ejercicio principal para desarrollo de hombros. Excelente para fuerza y masa en deltoides.',
                'instructions': ['Barra apoyada en la parte alta del pecho', 'Agarre ligeramente más ancho que los hombros', 'Empujar la barra verticalmente hacia arriba', 'Extender completamente los brazos', 'Bajar controladamente'],
                'tips': ['No arquees excesivamente la espalda', 'Mantén el core activado y contraído', 'Empuja la cabeza ligeramente hacia adelante al subir', 'Respiración: exhala al empujar'],
                'variations': ['Dumbbell Shoulder Press', 'Arnold Press', 'Seated Shoulder Press'],
            },
            {
                'id': 'incline-press',
                'name': 'Press Inclinado',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/10/incline-barbell-bench-press.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Incline-Bench-Press.gif',
                'equipments': 'Barra',
                'bodyParts': 'Pecho',
                'targetMuscles': 'Pectorales superiores',
                'secondaryMuscles': 'Deltoides, Tríceps',
                'overview': 'Variante del press que enfatiza la parte superior del pecho.',
                'instructions': ['Banco inclinado 30-45 grados', 'Agarrar barra', 'Bajar al pecho superior', 'Empujar hacia arriba'],
                'tips': ['No inclines demasiado el banco', 'Mantén escápulas retraídas'],
                'variations': ['Dumbbell Incline Press', 'Low Incline Press'],
            },
            {
                'id': 'push-up',
                'name': 'Flexiones',
                'imageUrl': 'https://hips.hearstapps.com/hmg-prod/images/workouts/2016/03/pushup-1457021003.gif',
                'gifUrl': 'https://hips.hearstapps.com/hmg-prod/images/workouts/2016/03/pushup-1457021003.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Pecho',
                'targetMuscles': 'Pectorales',
                'secondaryMuscles': 'Tríceps, Core',
                'overview': 'Ejercicio clásico de peso corporal para pecho, brazos y core.',
                'instructions': ['Posición de plancha', 'Manos al ancho de hombros', 'Bajar hasta casi tocar el suelo', 'Empujar hacia arriba'],
                'tips': ['Core contraído', 'Cuerpo en línea recta', 'Codos 45 grados'],
                'variations': ['Diamond Push-ups', 'Wide Push-ups', 'Decline Push-ups'],
            },
            
            # ========== PIERNAS ========== (evitar duplicados con pecho)
            {
                'id': 'leg-press',
                'name': 'Prensa de Piernas',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/leg-press.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/45-Degree-Leg-Press.gif',
                'equipments': 'Máquina',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Cuádriceps',
                'secondaryMuscles': 'Glúteos',
                'overview': 'Ejercicio en máquina para desarrollo de piernas con carga alta.',
                'instructions': ['Sentarse en máquina', 'Pies en plataforma', 'Bajar controlado', 'Empujar con fuerza'],
                'tips': ['No despegues la espalda baja', 'Rodillas sin bloqueo completo'],
                'variations': ['Single Leg Press', 'Narrow Stance'],
            },
            {
                'id': 'lunges',
                'name': 'Zancadas',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-dumbbell-lunge.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-dumbbell-lunge.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Cuádriceps',
                'secondaryMuscles': 'Glúteos, Femorales',
                'overview': 'Ejercicio unilateral excelente para piernas y equilibrio.',
                'instructions': ['De pie con mancuernas', 'Paso grande adelante', 'Bajar hasta rodilla casi toca suelo', 'Volver posición inicial'],
                'tips': ['Rodilla delantera no pasa la punta del pie', 'Torso erguido'],
                'variations': ['Reverse Lunges', 'Walking Lunges'],
            },
            {
                'id': 'leg-curl',
                'name': 'Curl Femoral',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-lying-leg-curl.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-lying-leg-curl.gif',
                'equipments': 'Máquina',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Femorales',
                'secondaryMuscles': 'Gemelos',
                'overview': 'Aislamiento de femorales en máquina.',
                'instructions': ['Acostarse boca abajo', 'Talones bajo rodillos', 'Flexionar piernas', 'Bajar controlado'],
                'tips': ['No despegues las caderas', 'Contracción en la parte superior'],
                'variations': ['Seated Leg Curl', 'Standing Leg Curl'],
            },
            
            # ========== ESPALDA ========== (evitar duplicados)
            {
                'id': 'barbell-row',
                'name': 'Remo con Barra',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2021/06/Barbell-Bent-Over-Row.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bent-Over-Row.gif',
                'equipments': 'Barra',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Dorsales',
                'secondaryMuscles': 'Romboides, Bíceps',
                'overview': 'Ejercicio de tracción horizontal para espalda media.',
                'instructions': ['Inclinarse 45 grados', 'Barra en manos', 'Tirar hacia abdomen', 'Bajar controlado'],
                'tips': ['Espalda recta', 'Contrae escápulas'],
                'variations': ['Underhand Row', 'Yates Row'],
            },
            {
                'id': 'lat-pulldown',
                'name': 'Jalón al Pecho',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2023/03/wide-grip-lat-pulldown.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Lat-Pulldown.gif',
                'equipments': 'Máquina',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Dorsales',
                'secondaryMuscles': 'Bíceps',
                'overview': 'Ejercicio de tracción en máquina, excelente para construir dorsales.',
                'instructions': ['Sentarse en máquina', 'Agarrar barra ancha', 'Tirar hasta pecho', 'Subir controlado'],
                'tips': ['Pecho hacia afuera', 'No usar impulso'],
                'variations': ['Close Grip Pulldown', 'Reverse Grip'],
            },
            
            # ========== HOMBROS ========== (El Press Militar ya está en sección principal)
            {
                'id': 'lateral-raise',
                'name': 'Elevaciones Laterales',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/09/dumbbell-lateral-raise.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Hombros',
                'targetMuscles': 'Deltoides lateral',
                'secondaryMuscles': 'Trapecio',
                'overview': 'Aislamiento para deltoides lateral, crea hombros anchos.',
                'instructions': ['De pie con mancuernas', 'Elevar a los lados', 'Hasta altura hombros', 'Bajar lento'],
                'tips': ['No subir demasiado', 'Control total'],
                'variations': ['Cable Lateral Raise', 'Bent Over Lateral Raise'],
            },
            {
                'id': 'front-raise',
                'name': 'Elevaciones Frontales',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/dumbbell-front-raise.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Front-Raise.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Hombros',
                'targetMuscles': 'Deltoides frontal',
                'secondaryMuscles': 'Pecho superior',
                'overview': 'Aislamiento para la parte frontal de los hombros.',
                'instructions': ['Mancuernas al frente de muslos', 'Elevar al frente', 'Hasta altura ojos', 'Bajar controlado'],
                'tips': ['No usar impulso', 'Movimiento controlado'],
                'variations': ['Barbell Front Raise', 'Alternating Front Raise'],
            },
            
            # ========== BRAZOS ==========
            {
                'id': 'bicep-curl',
                'name': 'Curl de Bíceps',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/standing-dumbbell-curl.gif',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Curl.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Bíceps',
                'secondaryMuscles': 'Braquial, Antebrazos',
                'overview': 'Ejercicio de aislamiento clásico para bíceps.',
                'instructions': ['Mancuernas a los lados', 'Codos fijos', 'Curvar arriba', 'Bajar controlado'],
                'tips': ['NO usar impulso', 'Codos fijos', 'Contracción arriba'],
                'variations': ['Hammer Curl', 'Preacher Curl'],
            },
            {
                'id': 'tricep-dips',
                'name': 'Fondos de Tríceps',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/tricep-dips.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Bench-Dips.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Tríceps',
                'secondaryMuscles': 'Pecho, Hombros',
                'overview': 'Ejercicio compuesto con peso corporal para tríceps.',
                'instructions': ['En barras paralelas', 'Bajar flexionando codos', 'Hasta 90 grados', 'Subir extendiendo'],
                'tips': ['Codos hacia atrás', 'No bajar demasiado'],
                'variations': ['Bench Dips', 'Weighted Dips'],
            },
            {
                'id': 'tricep-extension',
                'name': 'Extensiones de Tríceps',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-overhead-dumbbell-triceps-extension.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-overhead-dumbbell-triceps-extension.gif',
                'equipments': 'Mancuerna',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Tríceps',
                'secondaryMuscles': '',
                'overview': 'Aislamiento puro de tríceps, enfatiza la cabeza larga.',
                'instructions': ['Mancuerna sobre cabeza', 'Bajar detrás de cabeza', 'Extender arriba', 'Repetir'],
                'tips': ['Codos fijos apuntando arriba', 'Movimiento solo de codos'],
                'variations': ['Cable Overhead Extension', 'Barbell Extension'],
            },
            {
                'id': 'hammer-curl',
                'name': 'Curl Martillo',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/hammer-curl.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Hammer-Curl.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Bíceps, Braquial',
                'secondaryMuscles': 'Antebrazos',
                'overview': 'Variante de curl que enfatiza braquial y antebrazos.',
                'instructions': ['Mancuernas con agarre neutro', 'Curvar hacia hombros', 'Contraer', 'Bajar'],
                'tips': ['Mantén agarre neutro', 'Codos fijos'],
                'variations': ['Cross Body Hammer Curl', 'Cable Hammer Curl'],
            },
            
            # ========== ABDOMEN/CORE ==========
            {
                'id': 'plank',
                'name': 'Plancha',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-plank.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-plank.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Abdominales',
                'secondaryMuscles': 'Core completo',
                'overview': 'Ejercicio isométrico fundamental para core y estabilidad.',
                'instructions': ['Posición de antebrazo', 'Cuerpo recto', 'Mantener posición', 'Respirar normal'],
                'tips': ['No dejes caer cadera', 'Core contraído'],
                'variations': ['Side Plank', 'Plank with Leg Lift'],
            },
            {
                'id': 'crunches',
                'name': 'Abdominales',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-crunch.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-crunch.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Recto abdominal',
                'secondaryMuscles': '',
                'overview': 'Ejercicio clásico para abdominales.',
                'instructions': ['Acostado boca arriba', 'Manos en cabeza', 'Elevar torso', 'Bajar controlado'],
                'tips': ['No jalar el cuello', 'Contrae abdomen'],
                'variations': ['Bicycle Crunches', 'Reverse Crunches'],
            },
            {
                'id': 'russian-twist',
                'name': 'Giros Rusos',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-russian-twist.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-russian-twist.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Oblicuos',
                'secondaryMuscles': 'Abdominales',
                'overview': 'Ejercicio de rotación para oblicuos y core.',
                'instructions': ['Sentado con pies elevados', 'Rotar torso a los lados', 'Tocar suelo con manos', 'Alternar lados'],
                'tips': ['Mantén pies elevados', 'Movimiento controlado'],
                'variations': ['Weighted Russian Twist', 'Standing Russian Twist'],
            },
            
            # ========== MÁS EJERCICIOS VARIADOS ==========
            
            # PECHO
            {
                'id': 'dumbbell-fly',
                'name': 'Aperturas con Mancuernas',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/dumbbell-fly.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Fly.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Pecho',
                'targetMuscles': 'Pectorales',
                'secondaryMuscles': 'Deltoides anterior',
                'overview': 'Ejercicio de aislamiento para pecho, excelente para el estiramiento.',
                'instructions': ['Acostado en banco plano', 'Mancuernas arriba con brazos extendidos', 'Bajar abriendo brazos en arco', 'Subir contrayendo pecho'],
                'tips': ['Mantén ligera flexión en codos', 'No bajar demasiado'],
                'variations': ['Incline Fly', 'Cable Fly'],
            },
            {
                'id': 'decline-press',
                'name': 'Press Declinado',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-decline-bench-press.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-decline-bench-press.gif',
                'equipments': 'Barra',
                'bodyParts': 'Pecho',
                'targetMuscles': 'Pectorales inferiores',
                'secondaryMuscles': 'Tríceps',
                'overview': 'Variante que enfatiza la parte inferior del pecho.',
                'instructions': ['Banco declinado 15-30 grados', 'Bajar barra al pecho inferior', 'Empujar hacia arriba'],
                'tips': ['Pies bien asegurados', 'No arquear espalda'],
                'variations': ['Dumbbell Decline Press'],
            },
            
            # PIERNAS
            {
                'id': 'romanian-deadlift',
                'name': 'Peso Muerto Rumano',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/barbell-romanian-deadlift.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Romanian-Deadlift.gif',
                'equipments': 'Barra',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Femorales',
                'secondaryMuscles': 'Glúteos, Espalda baja',
                'overview': 'Variante que enfatiza femorales y glúteos.',
                'instructions': ['De pie con barra', 'Bajar con piernas casi rectas', 'Sentir estiramiento en femorales', 'Subir con cadera'],
                'tips': ['Espalda siempre recta', 'Barra pegada a piernas'],
                'variations': ['Single Leg Romanian Deadlift'],
            },
            {
                'id': 'leg-extension',
                'name': 'Extensiones de Pierna',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/leg-extension.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/LEG-EXTENSION.gif',
                'equipments': 'Máquina',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Cuádriceps',
                'secondaryMuscles': '',
                'overview': 'Aislamiento puro de cuádriceps.',
                'instructions': ['Sentado en máquina', 'Extender piernas hacia arriba', 'Contraer cuádriceps', 'Bajar controlado'],
                'tips': ['No usar impulso', 'Contracción al final'],
                'variations': ['Single Leg Extension'],
            },
            {
                'id': 'calf-raise',
                'name': 'Elevaciones de Gemelos',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-standing-calf-raises.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-standing-calf-raises.gif',
                'equipments': 'Barra o Máquina',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Gemelos',
                'secondaryMuscles': 'Sóleo',
                'overview': 'Ejercicio principal para desarrollar gemelos.',
                'instructions': ['De pie con peso', 'Elevar talones lo más alto posible', 'Contraer gemelos arriba', 'Bajar hasta estirar'],
                'tips': ['Rango completo de movimiento', 'Pausa arriba'],
                'variations': ['Seated Calf Raise', 'Single Leg Calf Raise'],
            },
            {
                'id': 'bulgarian-split-squat',
                'name': 'Sentadilla Búlgara',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-bulgarian-split-squat.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-bulgarian-split-squat.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Cuádriceps, Glúteos',
                'secondaryMuscles': 'Femorales',
                'overview': 'Ejercicio unilateral excelente para piernas y equilibrio.',
                'instructions': ['Pie trasero elevado en banco', 'Bajar flexionando pierna delantera', 'Hasta rodilla casi toca suelo', 'Subir con fuerza'],
                'tips': ['Torso erguido', 'Rodilla no pasa punta de pie'],
                'variations': ['Barbell Bulgarian Split Squat'],
            },
            
            # ESPALDA
            {
                'id': 'cable-row',
                'name': 'Remo en Polea',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-cable-seated-row.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-cable-seated-row.gif',
                'equipments': 'Polea',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Dorsales',
                'secondaryMuscles': 'Romboides, Bíceps',
                'overview': 'Ejercicio de tracción con tensión constante.',
                'instructions': ['Sentado frente a polea', 'Tirar hacia abdomen', 'Contraer escápulas', 'Volver controlado'],
                'tips': ['Espalda recta', 'No usar espalda baja'],
                'variations': ['Wide Grip Cable Row', 'Single Arm Cable Row'],
            },
            {
                'id': 'face-pull',
                'name': 'Face Pull',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/cable-face-pull.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Face-Pull.gif',
                'equipments': 'Polea',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Deltoides posterior',
                'secondaryMuscles': 'Romboides, Trapecio',
                'overview': 'Excelente para hombros posteriores y postura.',
                'instructions': ['Polea alta con cuerda', 'Tirar hacia cara', 'Separar manos al final', 'Contraer espalda'],
                'tips': ['Codos altos', 'Apretar escápulas'],
                'variations': ['Band Face Pull'],
            },
            {
                'id': 'shrug',
                'name': 'Encogimientos de Hombros',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/barbell-shrug.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Shrug.gif',
                'equipments': 'Barra',
                'bodyParts': 'Espalda',
                'targetMuscles': 'Trapecios',
                'secondaryMuscles': '',
                'overview': 'Aislamiento para trapecios superiores.',
                'instructions': ['De pie con barra', 'Elevar hombros hacia orejas', 'Contraer trapecios arriba', 'Bajar controlado'],
                'tips': ['No rotar hombros', 'Solo movimiento vertical'],
                'variations': ['Dumbbell Shrug', 'Behind Back Shrug'],
            },
            
            # HOMBROS
            {
                'id': 'upright-row',
                'name': 'Remo Alto',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/barbell-upright-row.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Upright-Row.gif',
                'equipments': 'Barra',
                'bodyParts': 'Hombros',
                'targetMuscles': 'Deltoides, Trapecios',
                'secondaryMuscles': 'Bíceps',
                'overview': 'Ejercicio compuesto para hombros y trapecios.',
                'instructions': ['De pie con barra', 'Tirar hacia barbilla', 'Codos altos', 'Bajar controlado'],
                'tips': ['No subir demasiado alto', 'Agarre cómodo'],
                'variations': ['Dumbbell Upright Row', 'Cable Upright Row'],
            },
            {
                'id': 'rear-delt-fly',
                'name': 'Aperturas Posteriores',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-dumbbell-rear-delt-fly.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-dumbbell-rear-delt-fly.gif',
                'equipments': 'Mancuernas',
                'bodyParts': 'Hombros',
                'targetMuscles': 'Deltoides posterior',
                'secondaryMuscles': 'Romboides',
                'overview': 'Aislamiento para deltoides posterior.',
                'instructions': ['Inclinado hacia adelante', 'Elevar mancuernas a los lados', 'Contraer escápulas', 'Bajar lento'],
                'tips': ['Espalda recta', 'Codos ligeramente flexionados'],
                'variations': ['Machine Rear Delt Fly', 'Cable Rear Delt Fly'],
            },
            
            # BRAZOS
            {
                'id': 'preacher-curl',
                'name': 'Curl Predicador',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-ez-bar-preacher-curl.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-ez-bar-preacher-curl.gif',
                'equipments': 'Barra',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Bíceps',
                'secondaryMuscles': 'Braquial',
                'overview': 'Aislamiento estricto de bíceps.',
                'instructions': ['Brazos apoyados en banco predicador', 'Curvar barra hacia arriba', 'Contraer bíceps', 'Bajar controlado'],
                'tips': ['No despegar brazos del banco', 'Extensión completa'],
                'variations': ['Dumbbell Preacher Curl', 'Machine Preacher Curl'],
            },
            {
                'id': 'close-grip-press',
                'name': 'Press Cerrado',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-close-grip-bench-press.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-close-grip-bench-press.gif',
                'equipments': 'Barra',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Tríceps',
                'secondaryMuscles': 'Pecho, Hombros',
                'overview': 'Ejercicio compuesto para tríceps.',
                'instructions': ['Acostado en banco', 'Agarre angosto (ancho de hombros)', 'Bajar al pecho', 'Empujar con tríceps'],
                'tips': ['Codos pegados al cuerpo', 'No arquear espalda'],
                'variations': ['Dumbbell Close Grip Press'],
            },
            {
                'id': 'cable-pushdown',
                'name': 'Extensiones en Polea',
                'imageUrl': 'https://www.inspireusafoundation.org/wp-content/uploads/2022/02/tricep-pushdown.jpg',
                'gifUrl': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Pushdown.gif',
                'equipments': 'Polea',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Tríceps',
                'secondaryMuscles': '',
                'overview': 'Aislamiento de tríceps con tensión constante.',
                'instructions': ['Polea alta con barra', 'Empujar hacia abajo', 'Extender completamente', 'Volver controlado'],
                'tips': ['Codos fijos a los lados', 'No usar hombros'],
                'variations': ['Rope Pushdown', 'Reverse Grip Pushdown'],
            },
            {
                'id': 'concentration-curl',
                'name': 'Curl Concentrado',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-concentration-curl.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-concentration-curl.gif',
                'equipments': 'Mancuerna',
                'bodyParts': 'Brazos',
                'targetMuscles': 'Bíceps',
                'secondaryMuscles': '',
                'overview': 'Máximo aislamiento de bíceps.',
                'instructions': ['Sentado, codo apoyado en muslo', 'Curvar mancuerna hacia hombro', 'Contraer bíceps', 'Bajar lento'],
                'tips': ['Sin impulso', 'Concentración total'],
                'variations': ['Cable Concentration Curl'],
            },
            
            # CORE
            {
                'id': 'leg-raise',
                'name': 'Elevaciones de Pierna',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-leg-raise.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-leg-raise.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Abdominales inferiores',
                'secondaryMuscles': 'Hip flexors',
                'overview': 'Excelente para abdominales inferiores.',
                'instructions': ['Acostado boca arriba', 'Elevar piernas juntas', 'Hasta 90 grados', 'Bajar sin tocar suelo'],
                'tips': ['Presiona espalda baja al suelo', 'Movimiento controlado'],
                'variations': ['Hanging Leg Raise', 'Bent Knee Leg Raise'],
            },
            {
                'id': 'mountain-climber',
                'name': 'Escaladores',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-mountain-climber.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-mountain-climber.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Core completo',
                'secondaryMuscles': 'Hombros, Cardiovascular',
                'overview': 'Ejercicio dinámico para core y cardio.',
                'instructions': ['Posición de plancha', 'Llevar rodilla al pecho alternando', 'Mantener cadera baja', 'Ritmo rápido'],
                'tips': ['Core contraído siempre', 'No elevar cadera'],
                'variations': ['Cross Body Mountain Climbers'],
            },
            {
                'id': 'side-plank',
                'name': 'Plancha Lateral',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-side-plank.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-side-plank.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Oblicuos',
                'secondaryMuscles': 'Core, Hombros',
                'overview': 'Isométrico para oblicuos y estabilidad lateral.',
                'instructions': ['De lado en antebrazo', 'Cuerpo en línea recta', 'Cadera arriba', 'Mantener posición'],
                'tips': ['No dejar caer cadera', 'Contraer oblicuos'],
                'variations': ['Side Plank with Hip Dip', 'Extended Side Plank'],
            },
            {
                'id': 'bicycle-crunch',
                'name': 'Abdominales Bicicleta',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-bicycle-crunch.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-bicycle-crunch.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Abdominales, Oblicuos',
                'secondaryMuscles': '',
                'overview': 'Ejercicio completo para abdominales y oblicuos.',
                'instructions': ['Acostado con manos en cabeza', 'Llevar codo a rodilla opuesta alternando', 'Piernas en movimiento de bicicleta', 'Rotar torso'],
                'tips': ['No jalar cuello', 'Movimiento controlado'],
                'variations': ['Slow Bicycle Crunch'],
            },
            
            # CARDIO / FUNCIONAL
            {
                'id': 'burpee',
                'name': 'Burpees',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-burpee.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-burpee.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Core',
                'targetMuscles': 'Cuerpo completo',
                'secondaryMuscles': 'Cardiovascular',
                'overview': 'Ejercicio de cuerpo completo altamente demandante.',
                'instructions': ['De pie a sentadilla', 'Manos al suelo', 'Saltar a plancha', 'Flexión', 'Volver y saltar arriba'],
                'tips': ['Ritmo constante', 'Buena técnica'],
                'variations': ['Half Burpee', 'Box Jump Burpee'],
            },
            {
                'id': 'jump-squat',
                'name': 'Sentadilla con Salto',
                'imageUrl': 'https://homeworkouts.org/wp-content/uploads/anim-jump-squat.gif',
                'gifUrl': 'https://homeworkouts.org/wp-content/uploads/anim-jump-squat.gif',
                'equipments': 'Peso Corporal',
                'bodyParts': 'Piernas',
                'targetMuscles': 'Cuádriceps, Glúteos',
                'secondaryMuscles': 'Explosividad',
                'overview': 'Ejercicio pliométrico para potencia de piernas.',
                'instructions': ['Sentadilla profunda', 'Explotar hacia arriba', 'Saltar lo más alto posible', 'Aterrizar suave'],
                'tips': ['Aterrizaje controlado', 'Rodillas alineadas'],
                'variations': ['Weighted Jump Squat'],
            },
        ]
    
    @staticmethod
    def verificar_gif_valido(gif_url):
        """Verifica si un GIF es válido (no 404)"""
        if not gif_url or 'placeholder' in gif_url.lower():
            return False
        # Considerar válido si existe (evitar requests para no gastar API)
        return True
    
    @staticmethod
    def enriquecer_ejercicio_con_api(ejercicio):
        """Enriquece un ejercicio de respaldo con datos de la API si es necesario"""
        # Solo enriquecer si falta GIF o está roto
        if ExerciseDBService.verificar_gif_valido(ejercicio.get('gifUrl')):
            return ejercicio  # Ya tiene GIF válido
        
        try:
            # Buscar en API V2 por nombre
            nombre_buscar = ejercicio.get('name', '').lower()
            
            # Palabras clave para buscar en la API
            palabras_clave = nombre_buscar.split()[:2]  # Primeras 2 palabras
            
            if not palabras_clave:
                return ejercicio
            
            # Hacer búsqueda en API
            # (Aquí se podría implementar la búsqueda, pero para evitar gastar requests,
            #  mejor mantener los GIFs que ya funcionan)
            
        except Exception as e:
            print(f"⚠️ No se pudo enriquecer {ejercicio.get('name')}: {e}")
        
        return ejercicio
    
    @staticmethod
    def get_all_exercises(limit=100):
        """Obtiene ejercicios de ExerciseDB o usa respaldo"""
        
        # Si está configurado para usar solo respaldo, retornarlos directamente
        if ExerciseDBService.USE_FALLBACK_ONLY:
            print("ℹ️ Usando ejercicios de respaldo (modo offline)")
            return ExerciseDBService.get_fallback_exercises()[:limit]
        
        cache_key = f'exercisedb_all_{limit}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            # Llamar a la API de ExerciseDB
            # Documentación: https://www.exercisedb.dev/docs
            base_url = ExerciseDBService.BASE_URL_V1 if ExerciseDBService.USE_V1 else ExerciseDBService.BASE_URL_V2
            
            headers = {'User-Agent': 'GymFlow/1.0'}
            
            # Si usamos V2, agregar API key
            if not ExerciseDBService.USE_V1 and ExerciseDBService.API_KEY:
                headers['X-RapidAPI-Key'] = ExerciseDBService.API_KEY
                headers['X-RapidAPI-Host'] = 'exercisedb-api1.p.rapidapi.com'
            
            # V2 requiere /api/v1/ en la ruta, V1 no
            endpoint = f"{base_url}/api/v1/exercises" if not ExerciseDBService.USE_V1 else f"{base_url}/exercises"
            
            # Para V2, usar parámetro 'limit' correcto (máximo 200 por página)
            params = {}
            if not ExerciseDBService.USE_V1:
                # V2 usa paginación, máximo 200 por request
                params['limit'] = min(limit, 200)
            else:
                # V1 acepta límite directo
                params['limit'] = min(limit, 500)
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=15,
                headers=headers
            )
            
            print(f"✓ ExerciseDB API ({base_url}) - Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # V2 devuelve un objeto con 'data', V1 devuelve lista directa
                if isinstance(response_data, dict) and 'data' in response_data:
                    exercises = response_data['data']  # API V2
                    print(f"✓ API V2: {len(exercises)} ejercicios, Total: {response_data.get('meta', {}).get('total', 'N/A')}")
                elif isinstance(response_data, list):
                    exercises = response_data  # API V1
                else:
                    print(f"⚠️ La API devolvió {type(response_data)} en lugar de lista")
                    print(f"⚠️ Respuesta: {str(response_data)[:200]}...")
                    raise ValueError("API response format not recognized")
                
                # Transformar al formato de nuestra app
                result = []
                for ex in exercises:
                    # Verificar que cada ejercicio sea un diccionario
                    if not isinstance(ex, dict):
                        print(f"⚠️ Ejercicio no es diccionario: {type(ex)}")
                        continue
                    # API V1 y V2 pueden devolver URLs relativas o nombres de archivo
                    # Construir URLs completas según documentación ExerciseDB
                    # Referencia: https://github.com/ExerciseDB/exercisedb-api/tree/main/media
                    image_url = ex.get('imageUrl', '')
                    video_url = ex.get('videoUrl', '')
                    gif_url = ex.get('gifUrl', '')
                    exercise_id = ex.get('exerciseId', '')
                    
                    # Construir URLs completas para V1 (desde GitHub media)
                    if ExerciseDBService.USE_V1:
                        # V1 sirve medios desde GitHub
                        if image_url and not image_url.startswith('http'):
                            # Construir URL desde GitHub media
                            image_url = f'https://raw.githubusercontent.com/ExerciseDB/exercisedb-api/main/media/{image_url}'
                        
                        if gif_url and not gif_url.startswith('http'):
                            gif_url = f'https://raw.githubusercontent.com/ExerciseDB/exercisedb-api/main/media/{gif_url}'
                        elif not gif_url:
                            gif_url = image_url  # Usar imagen como fallback
                        
                        if video_url and not video_url.startswith('http'):
                            video_url = f'https://raw.githubusercontent.com/ExerciseDB/exercisedb-api/main/media/{video_url}'
                    else:
                        # V2 usa CDN propio
                        if image_url and not image_url.startswith('http') and exercise_id:
                            image_url = f'https://v2.exercisedb.io/image/{exercise_id}'
                        
                        if not gif_url:
                            gif_url = image_url
                        
                        if video_url and not video_url.startswith('http') and exercise_id:
                            video_url = f'https://v2.exercisedb.io/video/{exercise_id}'
                    
                    exercise = {
                        'id': ex.get('exerciseId', ''),
                        'name': traducir_texto(ex.get('name', '')),  # Traducir nombre
                        'imageUrl': image_url,
                        'gifUrl': image_url,  # V2 usa la misma imagen (puede ser GIF o PNG)
                        'videoUrl': video_url,
                        'equipments': traducir_texto(', '.join(ex.get('equipments', [])) if ex.get('equipments') else 'N/A'),
                        'bodyParts': traducir_texto(', '.join(ex.get('bodyParts', [])) if ex.get('bodyParts') else 'N/A'),
                        'targetMuscles': traducir_texto(', '.join(ex.get('targetMuscles', [])) if ex.get('targetMuscles') else 'N/A'),
                        'secondaryMuscles': traducir_texto(', '.join(ex.get('secondaryMuscles', [])) if ex.get('secondaryMuscles') else ''),
                        'overview': ex.get('overview', ''),  # Mantener descripción en inglés (muy largo para traducir)
                        'instructions': ex.get('instructions', []),
                        'tips': ex.get('exerciseTips', []),
                        'variations': ex.get('variations', []),
                    }
                    result.append(exercise)
                
                if result:
                    print(f"✓ Obtenidos {len(result)} ejercicios de ExerciseDB API")
                    
                    # Filtrar ejercicios comunes de gym (equipamiento típico)
                    ejercicios_gym = [
                        ex for ex in result 
                        if any(equipo in ex.get('equipments', '').lower() 
                               for equipo in ['barra', 'mancuerna', 'peso corporal', 'máquina', 'polea', 
                                            'barbell', 'dumbbell', 'body weight', 'machine', 'cable'])
                    ]
                    
                    # Si tenemos suficientes ejercicios de gym, usarlos
                    if len(ejercicios_gym) >= min(50, limit):
                        result = ejercicios_gym[:limit]
                        print(f"✓ Filtrados {len(result)} ejercicios comunes de gym")
                    
                    cache.set(cache_key, result, 86400)  # 24 horas
                    return result
                
        except Exception as e:
            print(f"⚠️ Error ExerciseDB API: {e}")
        
        # Usar ejercicios de respaldo
        print("⚠️ Usando ejercicios de respaldo")
        fallback = ExerciseDBService.get_fallback_exercises()
        return fallback[:limit]
    
    @staticmethod
    def get_exercise_by_id(exercise_id):
        """Obtiene un ejercicio específico"""
        # Primero buscar en ejercicios de respaldo
        fallback = ExerciseDBService.get_fallback_exercises()
        for ex in fallback:
            if ex['id'] == exercise_id:
                return ex
        
        # Si no está en respaldo y no usamos solo respaldo, intentar API
        if ExerciseDBService.USE_FALLBACK_ONLY:
            return None
        
        cache_key = f'exercisedb_{exercise_id}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        try:
            response = requests.get(
                f"{ExerciseDBService.BASE_URL}/exercises/{exercise_id}",
                timeout=10,
                headers={'User-Agent': 'GymFlow/1.0'}
            )
            
            if response.status_code == 200:
                ex = response.json()
                
                exercise = {
                    'id': ex.get('exerciseId', ''),
                    'name': ex.get('name', ''),
                    'imageUrl': ex.get('imageUrl', ''),
                    'videoUrl': ex.get('videoUrl', ''),
                    'equipments': ', '.join(ex.get('equipments', [])),
                    'bodyParts': ', '.join(ex.get('bodyParts', [])),
                    'targetMuscles': ', '.join(ex.get('targetMuscles', [])),
                    'secondaryMuscles': ', '.join(ex.get('secondaryMuscles', [])),
                    'overview': ex.get('overview', ''),
                    'instructions': ex.get('instructions', []),
                    'tips': ex.get('exerciseTips', []),
                    'variations': ex.get('variations', []),
                }
                
                cache.set(cache_key, exercise, 86400)
                return exercise
                
        except Exception as e:
            print(f"⚠️ Error al obtener ejercicio {exercise_id}: {e}")
        
        return None
    
    @staticmethod
    def search_exercises(query):
        """Busca ejercicios"""
        all_exercises = ExerciseDBService.get_all_exercises(limit=500)
        
        if not all_exercises:
            return []
        
        query = query.lower()
        
        return [
            ex for ex in all_exercises
            if query in ex.get('name', '').lower() 
            or query in ex.get('bodyParts', '').lower()
            or query in ex.get('targetMuscles', '').lower()
            or query in ex.get('equipments', '').lower()
        ]

