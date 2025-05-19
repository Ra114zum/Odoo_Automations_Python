for record in records:
    try:
        # Double-check required fields exist
        if not record.date_begin:
            _logger.warning(f"Skipping event {record.id} - No start date")
            continue
            
        # Create calendar event (with sudo to avoid permission issues)
        cal_event = env['calendar.event'].sudo().create({
            'name': record.name or "New Event",
            'start': record.date_begin,
            'stop': record.date_begin,  # Use same as start if no end date
            'user_id': record.user_id.id if record.user_id else env.uid,
            'description': record.description or "",
            'res_model': 'event.event',  # Link back to original event
            'res_id': record.id,
        })
        
        # Optional: Add activity log
        record.message_post(
            body=f"Automatically created calendar event: {cal_event.name}"
        )
        
    except Exception as e:
        _logger.error(f"Failed creating calendar event for {record.id}: {str(e)}")
        # Continue with next record even if one fails
        continue