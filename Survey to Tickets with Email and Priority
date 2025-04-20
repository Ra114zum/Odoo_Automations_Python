if env.context.get('active_model') == 'survey.user_input':
    record = env['survey.user_input'].browse(env.context.get('active_id'))
    
    if record and record.state == 'done':
        try:
            # Get survey title safely
            survey_title = record.survey_id.title or "Unnamed Survey"
            
            # Initialize variables
            email_cc = False
            ticket_priority = '3'  # Default to Low
            contact_info = {
                'email': record.partner_id.email if record.partner_id else False,
                'name': record.partner_id.name if record.partner_id else False,
            }
            
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
                    question = line.question_id.title.strip() if line.question_id.title else "Question"
                    answer = line.display_name.strip() if line.display_name else "No answer"
                    
                    # Capture email for CC
                    if "what is your email" in question.lower():
                        email_cc = answer
                        contact_info['email'] = answer
                    
                    # Detect priority from multiple choice
                    elif "priority" in question.lower():
                        if "high" in answer.lower():
                            ticket_priority = '1'
                        elif "medium" in answer.lower():
                            ticket_priority = '2'
                        elif "small" in answer.lower():
                            ticket_priority = '3'
                    
                    # Capture name
                    elif "name" in question.lower():
                        contact_info['name'] = answer
                    
                    description.extend([
                        "<tr>",
                        f"<td style='border:1px solid #ddd; padding:8px;'>{question}</td>",
                        f"<td style='border:1px solid #ddd; padding:8px;'>{answer}</td>",
                        "</tr>"
                    ])
            
            description.extend([
                "</table>",
                f"<p>Generated from survey response on {record.create_date}</p>",
                "</div>"
            ])
            
            # Create ticket
            ticket_vals = {
                'name': f"Survey: {survey_title}",
                'description': ''.join(description),
                'priority': ticket_priority,
                'team_id': 2,  # Your team ID
                'partner_id': record.partner_id.id if record.partner_id else False,
                'partner_email': contact_info['email'],
                'partner_name': contact_info['name'],
                'email_cc': email_cc,
            }
            
            env['helpdesk.ticket'].with_context(mail_create_nolog=True).create(ticket_vals)
            
        except Exception as e:
            # Simple error logging that won't fail
            error_message = f"Error processing survey {record.id if record else 'N/A'}: {str(e)}"
            env['helpdesk.ticket'].create({
                'name': "SURVEY PROCESSING ERROR",
                'description': error_message,
                'team_id': 2,
                'priority': '1'
            })
