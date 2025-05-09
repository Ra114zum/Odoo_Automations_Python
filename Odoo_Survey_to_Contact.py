if record.state == 'done':
    # Initialize variables
    partner_name = False
    partner_email = False
    survey_title = record.survey_id.title
    table_lines = [
        "<div style='margin-bottom:20px;'>",
        "<h3 style='color:#2c3e50;'>Survey: %s</h3>" % survey_title,
        "<table style='width:100%; border-collapse:collapse; margin-top:10px;'>",
        "<tr style='background-color: #f2f2f2;'>",
        "<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Question</th>",
        "<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Answer</th>",
        "</tr>"
    ]
    
    # Extract survey responses
    for line in record.user_input_line_ids:
        if line.question_id and line.display_name:
            question = line.question_id.title.strip()
            answer = line.display_name.strip()
            question_lower = question.lower()
            
            # Name detection
            if not partner_name and 'name' in question_lower:
                partner_name = answer.strip()
            
            # Email detection
            if not partner_email:
                if any(keyword in question_lower for keyword in ['email', 'e-mail', 'mail']):
                    if '@' in answer and '.' in answer.split('@')[-1]:
                        partner_email = answer.strip().lower()
                elif '@' in answer and '.' in answer.split('@')[-1]:  # Check answer even if question doesn't contain email keyword
                    partner_email = answer.strip().lower()
            
            table_lines.extend([
                "<tr>",
                "<td style='border: 1px solid #ddd; padding: 8px;'><strong>%s</strong></td>" % question,
                "<td style='border: 1px solid #ddd; padding: 8px;'>%s</td>" % answer,
                "</tr>"
            ])
    
    # Close table and div
    table_lines.extend(["</table>", "</div>"])
    survey_html = "".join(table_lines)
    
    # Find or create partner
    partner = False
    if partner_email:
        partner = env['res.partner'].search([('email', '=ilike', partner_email)], limit=1)
    
    # Prepare partner values
    partner_vals = {
        'comment': survey_html,
        'type': 'contact'
    }
    if partner_name:
        partner_vals['name'] = partner_name
    if partner_email:
        partner_vals['email'] = partner_email
    
    if partner:
        # Update existing partner
        partner_vals['comment'] = (partner.comment or "") + "<hr/>" + survey_html
        partner.write(partner_vals)
    else:
        # Create new partner if we have either name or email
        if partner_name or partner_email:
            # Set default name if not found in survey
            if not partner_name:
                partner_vals['name'] = partner_email or "Survey Respondent"
            env['res.partner'].create(partner_vals)
    
    # Optional: Link the survey response to the partner if needed
    if partner:
        record.write({'partner_id': partner.id})
        
        # Powered By HSx Tech


