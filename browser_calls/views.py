from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.voice_response import Pause, VoiceResponse, Say
from .models import SupportTicket


class SupportTicketCreate(SuccessMessageMixin, CreateView):
    """Renders the home page and the support ticket form"""

    model = SupportTicket
    fields = ['name', 'phone_number', 'description']
    template_name = 'index.html'
    success_url = reverse_lazy('home')
    success_message = "Your ticket was submitted! An agent will call you soon."


def support_dashboard(request):
    """Shows the list of support tickets to a support agent"""
    context = {}

    context['support_tickets'] = SupportTicket.objects.order_by('-timestamp')

    return render(request, 'browser_calls/support_dashboard.html', context)


def get_token(request):
    identity = 'support_agent' if 'dashboard' in request.GET['forPage'] else 'customer'

     #Create access token with credentials
    access_token = AccessToken(settings.TWILIO_ACCOUNT_SID, settings.API_KEY, settings.API_SECRET, identity=identity)

     #Create a Voice grant and add to token
    voice_grant = VoiceGrant(
        outgoing_application_sid=settings.TWIML_APPLICATION_SID,
        incoming_allow=True, # Optional: add to allow incoming calls
        #,
        #machine_detection='Enable'
    )
    access_token.add_grant(voice_grant)
    token = access_token.to_jwt()

    return JsonResponse({'token': token.decode('utf-8')})

@csrf_exempt
def call(request):
    """Returns TwiML instructions to Twilio's POST requests"""
    response = VoiceResponse()

    dial = response.dial(caller_id=settings.TWILIO_NUMBER)
    #response.say('I will pause 10 seconds starting now!')
    #response.pause(length=10)
    #response.say('I just paused 10 seconds')
    
        # If the browser sent a phoneNumber param, we know this request
    # is a support agent trying to call a customer's phone
    if 'phoneNumber' in request.POST:
        dial.number(request.POST['phoneNumber'])
    



    return HttpResponse(
        str(response), content_type='application/xml; charset=utf-8'
    )
