if env.context.get('active_model') == 'survey.user_input':
    record = env['survey.user_input'].browse(env.context.get('active_id'))
    
    if record and record.state == 'done':
        try:
            # Get survey title safely
            survey_title = record.survey_id.title or "Unnamed Survey"
            
            # Initialize variables
            email_cc = False
            ticket_priority = '3'  # Default to Low
            customer_email = False
            customer_name = "Survey Respondent"  # Default name
            team_id = 2  # Default to Odoo Team
            
            # Build description
            description = [
                "<div style='font-family: Arial, sans-serif;'>",
                f"<h3 style='color: #875A7B;'>{survey_title} Responses</h3>",
                "<table style='width:100%; border-collapse:collapse;'>",
                "<tr style='background-color:#f2f2f2;'>",
                "<th style='border:1px solid #ddd; padding:8px;'>Question</th>",
                "<th style='border:1px solid #ddd; padding:8px;'>Answer</th>",
                "</tr>"
            ]
            
            # Process each response line
            for line in record.user_input_line_ids:
                if line.question_id and line.display_name:
                    question = line.question_id.title.strip().lower()
                    answer = line.display_name.strip()
                    answer_lower = answer.lower()
                    
                    # Capture email for CC
                    if "email" in question:
                        email_cc = answer
                        customer_email = answer
                    
                    # PRIORITY DETECTION (EXACT MATCH)
                    elif "priority" in question:
                        if answer_lower == "high":
                            ticket_priority = '3'
                        elif answer_lower == "medium":
                            ticket_priority = '2'
                        elif answer_lower == "low":
                            ticket_priority = '1'
                    
                    # TEAM ASSIGNMENT (EXACT MATCH)
                    elif "team" in question:  # Changed to look for "team" in question
                        if answer == "Customer Care":  # Exact match for Customer Care
                            team_id = 1
                        elif answer == "Odoo Team":
                            team_id = 2
                        elif answer == "Developer Team":
                            team_id = 3
                        elif answer == "Urgent Meeting":
                            team_id = 4
                            ticket_priority = '1'  # Force High priority for Urgent Meeting
                    
                    # Capture name
                    elif "name" in question:
                        customer_name = answer or customer_name
                    
                    description.extend([
                        "<tr>",
                        f"<td style='border:1px solid #ddd; padding:8px;'>{line.question_id.title.strip()}</td>",
                        f"<td style='border:1px solid #ddd; padding:8px;'>{answer}</td>",
                        "</tr>"
                    ])
            
            description.extend([
                "</table>",
                f"<p>Generated from survey response on {record.create_date}</p>",
                f"<p>System Info: Priority={ticket_priority}, Team={team_id}</p>",
                "</div>"
            ])
            
            # GUARANTEED CUSTOMER CREATION
            partner_id = record.partner_id.id if record.partner_id else False
            
            if customer_email and not partner_id:
                # Clean email and name
                clean_email = customer_email.strip().lower()
                clean_name = customer_name.strip()
                
                # Find or create partner
                partner = env['res.partner'].search([('email', '=ilike', clean_email)], limit=1)
                
                if partner:
                    partner_id = partner.id
                    if clean_name and partner.name != clean_name:
                        partner.write({'name': clean_name})
                else:
                    partner = env['res.partner'].create({
                        'name': clean_name,
                        'email': clean_email,
                        'company_type': 'person'
                    })
                    partner_id = partner.id
            
            # Create ticket
            ticket_vals = {
                'name': f"Survey: {survey_title}",
                'description': ''.join(description),
                'priority': ticket_priority,
                'team_id': team_id,  # Dynamically assigned team
                'partner_id': partner_id,
                'partner_email': customer_email or (record.partner_id.email if record.partner_id else False),
                'partner_name': customer_name or (record.partner_id.name if record.partner_id else False),
                'email_cc': email_cc,
            }
            
            env['helpdesk.ticket'].with_context(mail_create_nolog=True).create(ticket_vals)
            
        except Exception as e:
            # Minimal error handling
            env['helpdesk.ticket'].create({
                'name': "SURVEY PROCESSING ERROR",
                'description': f"Error: {str(e)[:200]}",
                'team_id': 2,
                'priority': '1'
            })
