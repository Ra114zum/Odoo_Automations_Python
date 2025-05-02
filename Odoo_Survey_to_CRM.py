if record.state == 'done':
    # Initialize variables
    email_from = contact_name = False
    table_lines = [
        "<table style='width:100%; border-collapse:collapse; margin-top:20px;'>",
        "<caption style='font-weight:bold; margin-bottom:10px;'>",
        f"{record.survey_id.title} - {datetime.datetime.now().strftime('%Y-%m-%d')}",
        "</caption>",
        "<tr style='background-color:#f2f2f2;'>",
        "<th style='border:1px solid #ddd; padding:8px;'>Question</th>",
        "<th style='border:1px solid #ddd; padding:8px;'>Answer</th>",
        "</tr>"
    ]

    # Process survey responses
    for line in record.user_input_line_ids:
        if line.question_id and line.display_name:
            question = line.question_id.title.strip()
            answer = line.display_name.strip()
            
            # Email detection
            if any(kw in question.lower() for kw in ['email','e-mail','mail']) and '@' in answer:
                email_from = answer.split('@')[0].strip() + '@' + answer.split('@')[-1].strip()
            
            # Contact name detection
            question_lower = question.lower()
            if all(kw in question_lower for kw in ['contact', 'one', 'name']):
                contact_name = answer.strip()
            
            table_lines.extend([
                "<tr>",
                f"<td style='border:1px solid #ddd; padding:8px;'>{question}</td>",
                f"<td style='border:1px solid #ddd; padding:8px;'>{answer}</td>",
                "</tr>"
            ])

    # Prepare values
    lead_email = email_from or (record.partner_id.email if record.partner_id else None)
    survey_html = "".join(table_lines + ["</table>"])
    
    # Find matching leads (active or inactive)
    matching_leads = env['crm.lead'].search([
        '|', ('email_from', '=ilike', lead_email),
             ('partner_id.email', '=ilike', lead_email),
        ('type', '=', 'opportunity')
    ]) if lead_email else []

    if matching_leads:
        # Update most recently modified lead
        main_lead = matching_leads.sorted('write_date', reverse=True)[0]
        
        update_vals = {
            'description': f"{main_lead.description or ''}<hr/>{survey_html}",
            'active': True  # Reactivate if archived
        }
        if contact_name:
            update_vals['contact_name'] = contact_name
            
        main_lead.write(update_vals)
        
        # Log merge activity
        if len(matching_leads) > 1:
            main_lead.message_post(
                body=f"Combined with {len(matching_leads)-1} related opportunities",
                subject="Survey Response Added"
            )
    else:
        # Create new opportunity
        create_vals = {
            'name': f"{record.survey_id.title} - {lead_email or 'New Lead'}",
            'description': survey_html,
            'email_from': lead_email,
            'type': 'opportunity',
            'contact_name': contact_name or False
        }
        env['crm.lead'].create(create_vals)

        ## Powered By HSx Tech
        ## Ali and Muneeb