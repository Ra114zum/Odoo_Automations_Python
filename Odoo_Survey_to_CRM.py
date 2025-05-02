if record.state == 'done':
    # Initialize variables
    email_from = False
    contact_name = False
    survey_title = record.survey_id.title  # Get survey title
    table_lines = [
        "<div style='margin-bottom:20px;'>",
        "<h3 style='color:#2c3e50;'>Survey: %s</h3>" % survey_title,  # Added survey title display
        "<table style='width:100%; border-collapse:collapse; margin-top:10px;'>",
        "<tr style='background-color: #f2f2f2;'>",
        "<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Question</th>",
        "<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Answer</th>",
        "</tr>"
    ]
    
    # Detection patterns
    email_keywords = ['email', 'e-mail', 'mail']
    contact_keyphrases = [
        'contact name one',
        'contact name',
        'first name',
        'contact',
        'name',
        'one'
    ]
    
    # Extract survey responses
    for line in record.user_input_line_ids:
        if line.question_id and line.display_name:
            question = line.question_id.title.strip()
            answer = line.display_name.strip()
            question_lower = question.lower()
            
            # Email detection
            if not email_from and any(keyword in question_lower for keyword in email_keywords):
                if '@' in answer and '.' in answer.split('@')[-1]:
                    email_from = answer
            
            # Contact name detection (matches complete phrases first)
            if not contact_name:
                if 'contact name one' in question_lower:
                    contact_name = answer
                elif 'contact name' in question_lower:
                    contact_name = answer
                elif 'first name' in question_lower:
                    contact_name = answer
                elif any(keyword in question_lower for keyword in ['contact', 'name', 'one']):
                    contact_name = answer
            
            table_lines.extend([
                "<tr>",
                "<td style='border: 1px solid #ddd; padding: 8px;'><strong>%s</strong></td>" % question,
                "<td style='border: 1px solid #ddd; padding: 8px;'>%s</td>" % answer,
                "</tr>"
            ])
    
    # Close table and div
    table_lines.extend(["</table>", "</div>"])
    description = "".join(table_lines)
    
    # Fallback to partner email if no email found in survey
    lead_email = email_from or (record.partner_id.email if record.partner_id and record.partner_id.email else None)
    
    # Prepare opportunity name (now includes survey title)
    opportunity_name = "Opportunity from %s Survey" % survey_title  # Updated to use survey_title
    if lead_email:
        opportunity_name = "%s (%s)" % (opportunity_name, lead_email)
    
    # Find existing opportunities (excluding won stages)
    existing_opportunities = env['crm.lead'].search([
        ('email_from', '=', lead_email),
        ('type', '=', 'opportunity'),
        ('stage_id.is_won', '=', False),
    ]) if lead_email else env['crm.lead'].browse()
    
    if existing_opportunities:
        # Update most recent opportunity
        main_opportunity = existing_opportunities.sorted(key=lambda l: l.write_date or l.create_date, reverse=True)[0]
        other_opportunities = existing_opportunities - main_opportunity
        
        update_vals = {
            'description': "%s<hr/>%s" % (  # Simplified merging
                main_opportunity.description or "",
                description  # Already contains survey title and table
            )
        }
        if contact_name:
            update_vals['contact_name'] = contact_name
        
        main_opportunity.write(update_vals)
        
        # Handle other opportunities
        for opp in other_opportunities:
            env['mail.activity'].search([
                ('res_id', '=', opp.id),
                ('res_model', '=', 'crm.lead')
            ]).write({'res_id': main_opportunity.id})
            
            env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', opp.id)
            ]).write({'res_id': main_opportunity.id})
            
            opp.write({'active': False})
        
        main_opportunity.message_post(body="Merged with %d existing opportunities from %s survey" % (len(other_opportunities), survey_title))
    else:
        # Create new opportunity
        create_vals = {
            'name': opportunity_name,
            'description': description,  # Contains survey title and responses
            'email_from': lead_email,
            'type': 'opportunity',
        }
        if contact_name:
            create_vals['contact_name'] = contact_name
            
        env['crm.lead'].with_context(
            mail_create_nolog=True,
            tracking_disable=True
        ).create(create_vals)

## Powered By HSx Tech
## Ali and Muneeb
