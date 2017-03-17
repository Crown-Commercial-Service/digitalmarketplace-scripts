"""Spike script into mail chimp email sending."""
from mailchimp3 import MailChimp

from dmscripts.helpers.html_helpers import render_html

SPECIALISTS_CAMPAIGN_DATA = {
	"type": "regular",
	"recipients": {
		"list_id": "096e52cebb",  # test list containing one user (david mcdonald work email)
	},
	"settings": {
		"subject_line": "New opportunities for Digital Specialists: Digital Outcomes and Specialists 2",
		"title": "TEST! DOS Suppliers: Specialists [16 March]",
		"from_name": "Digital Marketplace Team",
		"reply_to": "do-not-reply@digitalmarketplace.service.gov.uk",
		"use_conversation": False,
		"authenticate": True,
		"auto_footer": False,
		"inline_css": False,
		"auto_tweet": False,
		"fb_comments": False
	},
	"tracking": {
		"opens": True,
		"html_clicks": True,
		"text_clicks": False,
		"goal_tracking": False,
		"ecomm360": False
	}
}

def get_html_content():
	email_body = render_html('email_templates/dos_opportunities.html', data={})
	return email_body

def create_campaign(mailchimp_client):
	try:
		res = mailchimp_client.campaigns.create(data=SPECIALISTS_CAMPAIGN_DATA)
		campaign_id = res['id']
	except Exception as e:
		print e

	SPECIALISTS_CONTENT_DATA = {
		"html": get_html_content()
	}

	try:
		mailchimp_client.campaigns.content.update(campaign_id=campaign_id, data=SPECIALISTS_CONTENT_DATA)
	except Exception as e:
		print e

	return campaign_id

def send_campaign(mailchimp_client, campaign_id):
	try:
		return client.campaigns.actions.send(campaign_id=campaign_id)
	except Exception as e:
		print e

def main(mailchimp_username, mailchimp_api_key):
	mailchimp_client = MailChimp(mailchimp_username, mailchimp_api_key)

	campaign_id = create_campaign(mailchimp_client)
	if not campaign_id:
		return False
	return True
