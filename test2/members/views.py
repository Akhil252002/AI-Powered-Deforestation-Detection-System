from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import CustomUser, Region, Town, ImageAnalysis, Result, LandType
from .forms import RegionForm, TownForm
from inference_sdk import InferenceHTTPClient
import cv2
from PIL import Image
import os
from django.core.files.storage import FileSystemStorage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from io import BytesIO
from reportlab.lib.utils import ImageReader
from django.utils import timezone

# Initialize InferenceHTTPClient
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="Ni83CEqHFGwjmoBGTqm8"
)

# Home Page View

def home(request):
    return render(request, 'home.html')

# User Login View
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.role == 'Admin':
                return redirect('admin_dashboard')
            elif user.role == 'Analyst':
                return redirect('analyst_dashboard')
            else:
                return redirect('research_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

# User Registration View
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")
        
        if CustomUser.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "error": "Username already exists"
            })

        # Check email already exists
        if CustomUser.objects.filter(email=email).exists():
            return render(request, "register.html", {
                "error": "Email already exists"
            })

        new_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            first_name=username,
            password=password,
            role=role
        )
        new_user.save()

        return redirect("user_login")

    return render(request, "register.html")

# Consolidated Admin Dashboard View
@login_required
@csrf_exempt
def admin_dashboard(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_user':
            user_id = request.POST.get('user_id')
            try:
                user = CustomUser.objects.get(id=user_id)
                if user == request.user:
                    return JsonResponse({'success': False, 'message': 'Cannot delete the current user'})
                user.delete()
                return JsonResponse({'success': True})
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'User not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        elif action == 'add_user':
            try:
                username = request.POST.get('username')
                password = request.POST.get('password')
                role = request.POST.get('role')
                CustomUser.objects.create_user(
                    username=username,
                    password=password,
                    role=role
                )
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        elif action == 'logout_user':
            try:
                request.user.is_active = False
                request.user.save()
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
        return JsonResponse({'success': False, 'message': 'Invalid action'})

    # Get user statistics
    total_users = CustomUser.objects.count()
    analyst_count = CustomUser.objects.filter(role='Analyst').count()
    research_count = CustomUser.objects.filter(role='Research').count()
    
    # Get user data
    all_users = CustomUser.objects.all()
    analysts = CustomUser.objects.filter(role='Analyst')
    researchers = CustomUser.objects.filter(role='Research')
    
    # Get results with images
    results = Result.objects.all().order_by('-id')
    
    context = {
        'total_users': total_users,
        'analyst_count': analyst_count,
        'research_count': research_count,
        'all_users': all_users,
        'analysts': analysts,
        'researchers': researchers,
        'identifications': results,
    }
    
    return render(request, 'admin_dashboard.html', context)

# Add Region View (Admin Only)
def add_region(request):
    if request.method == "POST":
        region_name = request.POST.get("region_name")
        town_name = request.POST.get("town_name")
        land_type_name = request.POST.get("land_type")

        region = Region.objects.create(name=region_name)
        town = Town.objects.create(name=town_name, region=region)
        LandType.objects.create(town=town, land_type=land_type_name)

        return redirect("success_page")  # Adjust to your success page URL

    return render(request, "add_region.html")

# Add Region and Town View
def add_region_town(request):
    if request.method == 'POST':
        region_name = request.POST.get('region_name')
        town_name = request.POST.get('town_name')
        land_type = request.POST.get('land_type')

        Region.objects.create(
            name=region_name,
            region_type=land_type,
        )
        return redirect('admin_dashboard')

    return render(request, 'add_region.html')

# Analyst Dashboard View
@login_required
def analyst_dashboard(request):
    user_count = CustomUser.objects.count()
    region_count = ImageAnalysis.objects.values('region').distinct().count()
    forest_count = ImageAnalysis.objects.count()
    
    detection_trends = (ImageAnalysis.objects
                       .values('region', 'identifications')
                       .exclude(identifications__isnull=True)
                       .exclude(identifications__exact='')
                       .order_by('region')
                       .distinct())
    
    processed_trends = []
    for trend in detection_trends:
        identifications = trend['identifications'].split(',') if trend['identifications'] else []
        processed_trends.append({
            'region': trend['region'],
            'identifications': ', '.join(filter(None, identifications))
        })
    
    context = {
        'user_count': user_count,
        'region_count': region_count,
        'forest_count': forest_count,
        'detection_trends': processed_trends,
    }
    
    return render(request, 'analyst_dashboard.html', context)

# Researcher Dashboard View
def research_dashboard(request):
    results = Result.objects.all().order_by('-id')
    analyses = ImageAnalysis.objects.all().order_by('-id')
    
    combined_results = []
    for result in results:
        analysis = analyses.filter(region__iexact=result.region).first()
        combined_results.append({
            'id': result.id,
            'image': result.image,
            'region': result.region,
            'prediction': result.prediction,
            'identifications': analysis.identifications if analysis else 'No findings available'
        })
    
    context = {
        'results': combined_results,
    }
    return render(request, 'research_dashboard.html', context)

# Logout View
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("home")

# Image Upload and Processing View
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_file = request.FILES['image']
        region = request.POST.get('region').strip()
        identifications = request.POST.get('identifications', '').strip()

        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        image_path = fs.path(filename)

        try:
            region_entry, created = ImageAnalysis.objects.get_or_create(
                region__iexact=region,
                defaults={'region': region, 'identifications': identifications}
            )
            if not created and identifications:
                region_entry.identifications = identifications
                region_entry.save()

            result = CLIENT.infer(image_path, model_id="ic-i8d9e/1")    
            predictions = result['predictions']
            
            predicted_classes = {pred['class'] for pred in predictions}

            stored_classes = set(cls.strip() for cls in region_entry.identifications.split(","))

            match = predicted_classes == stored_classes
            match_result = "Match Found" if match else "Mismatch"

            Result.objects.create(
                region=region,
                prediction=",".join(predicted_classes),
                image=uploaded_file
            )

            return render(request, 'upload1.html', {
                'region': region,
                'predicted_classes': predicted_classes,
                'stored_classes': stored_classes,
                'match_result': match_result
            })

        except Exception as e:
            return render(request, 'upload1.html', {'error': str(e)})

    return render(request, 'upload1.html')

# Upload and Process View
def upload_and_process(request):
    if request.method == 'POST':
        region = request.POST.get('region')
        identifications = request.POST.get('identifications')

        ImageAnalysis.objects.create(region=region, identifications=identifications)

        return render(request, 'upload.html', {
            'message': 'Data saved successfully!',
        })

    return render(request, 'upload.html')

# User Count Views
def user_count_view(request):
    user_count = CustomUser.objects.count()
    return render(request, 'user_count.html', {'user_count': user_count})

def total_users_count(request):
    return JsonResponse({'count': CustomUser.objects.count()})

# Region Count Views
def region_count_view(request):
    region_count = Region.objects.count()  # Use Region model, not ImageAnalysis
    return render(request, 'admin_dashboard.html', {'region_count': region_count})

def total_region_count(request):
    return JsonResponse({'count': Region.objects.count()})

# Forest Count Views
def forest_count_view(request):
    forest_count = ImageAnalysis.objects.count()
    return render(request, 'admin_dashboard.html', {'forest_count': forest_count})

def total_forest_count(request):
    return JsonResponse({'count': ImageAnalysis.objects.count()})

# List Views
def users_list(request):
    users = CustomUser.objects.all()
    return render(request, 'users_list.html', {'users': users})

def regions_list(request):
    regions = ImageAnalysis.objects.all().values()
    return render(request, 'regions_list.html', {'regions': regions})

def region(request):
    regions = ImageAnalysis.objects.all().values()
    return render(request, 'region.html', {'regions': regions})

def forests_list(request):
    forests = ImageAnalysis.objects.all()
    return render(request, 'forests_list.html', {'forests': forests})

# Admin Management Views
@login_required
def admin_users(request):
    users = CustomUser.objects.all().order_by('role', 'date_joined')
    context = {
        'users': users,
        'section': 'users',
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'inactive_users': users.filter(is_active=False).count()
    }
    return render(request, 'admin/users.html', context)

@login_required
def admin_analysts(request):
    analysts = CustomUser.objects.filter(role='Analyst').order_by('date_joined')
    context = {
        'analysts': analysts,
        'section': 'analysts',
        'total_analysts': analysts.count(),
        'active_analysts': analysts.filter(is_active=True).count()
    }
    return render(request, 'admin/analysts.html', context)

@login_required
def admin_researchers(request):
    researchers = CustomUser.objects.filter(role='Research').order_by('date_joined')
    context = {
        'researchers': researchers,
        'section': 'researchers',
        'total_researchers': researchers.count(),
        'active_researchers': researchers.filter(is_active=True).count()
    }
    return render(request, 'admin/researchers.html', context)

@login_required
def admin_regions(request):
    regions = ImageAnalysis.objects.values('region').distinct()
    context = {
        'regions': regions,
        'section': 'regions',
        'total_regions': regions.count()
    }
    return render(request, 'admin/regions.html', context)

@login_required
def admin_forests(request):
    forests = ImageAnalysis.objects.all()
    context = {
        'forests': forests,
        'section': 'forests',
        'total_forests': forests.count()
    }
    return render(request, 'admin/forests.html', context)

@login_required
def admin_identifications(request):
    identifications = ImageAnalysis.objects.exclude(identifications='')
    context = {
        'identifications': identifications,
        'section': 'identifications',
        'total_identifications': identifications.count()
    }
    return render(request, 'admin/identifications.html', context)

# Download Report View
def download_report(request, result_id):
    try:
        result = Result.objects.get(id=result_id)
        analysis = ImageAnalysis.objects.filter(region__iexact=result.region).first()

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="report_{result.region}.pdf"'
        
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        y_position = height - 50
        
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, y_position, "Deforestation Analysis Report")
        
        y_position -= 30
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, f"Region: {result.region}")
        
        y_position -= 25
        p.setFont("Helvetica", 12)
        p.drawString(50, y_position, f"Prediction: {result.prediction}")
        
        if analysis:
            y_position -= 25
            p.drawString(50, y_position, f"Deforestation Findings: {analysis.identifications}")

        if result.image:
            img_path = result.image.path
            img = Image.open(img_path)
            aspect = img.width / img.height
            
            img_width = 350
            img_height = img_width / aspect
            
            y_position -= 20
            
            x_position = (width - img_width) / 2
            
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            p.drawImage(ImageReader(img_buffer), x_position, y_position - img_height, width=img_width, height=img_height)

        p.setFont("Helvetica", 10)
        p.drawString(50, 30, f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")

        p.save()
        return response

    except Result.DoesNotExist:
        return HttpResponse("Report not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating report: {str(e)}", status=500)