"""Contacts access via macOS CNContactStore (PyObjC).

Extracted from imessage-mcp and extended with search, get, create, update.
"""

from __future__ import annotations

import phonenumbers

_store_initialized = False
_store = None


def _init_store():
    """Initialize CNContactStore. Prompts for Contacts permission on first call."""
    global _store_initialized, _store  # noqa: PLW0603
    if _store_initialized:
        return
    _store_initialized = True
    try:
        from Contacts import CNContactStore  # type: ignore[import-untyped]

        _store = CNContactStore.alloc().init()
    except Exception:
        _store = None


def _normalize_phone(phone: str) -> str | None:
    """Normalize phone number to E.164 format for consistent matching."""
    try:
        parsed = phonenumbers.parse(phone, "US")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return phone


def _all_keys():
    """Return the standard set of fetch keys for contact details."""
    from Contacts import (  # type: ignore[import-untyped]
        CNContactBirthdayKey,
        CNContactEmailAddressesKey,
        CNContactFamilyNameKey,
        CNContactFormatter,
        CNContactFormatterStyleFullName,
        CNContactGivenNameKey,
        CNContactJobTitleKey,
        CNContactMiddleNameKey,
        CNContactNoteKey,
        CNContactOrganizationNameKey,
        CNContactPhoneNumbersKey,
        CNContactPostalAddressesKey,
        CNContactUrlAddressesKey,
    )

    return [
        CNContactGivenNameKey,
        CNContactMiddleNameKey,
        CNContactFamilyNameKey,
        CNContactOrganizationNameKey,
        CNContactJobTitleKey,
        CNContactPhoneNumbersKey,
        CNContactEmailAddressesKey,
        CNContactPostalAddressesKey,
        CNContactUrlAddressesKey,
        CNContactBirthdayKey,
        CNContactNoteKey,
        CNContactFormatter.descriptorForRequiredKeysForStyle_(CNContactFormatterStyleFullName),
    ]


def _format_contact(contact) -> str:
    """Format a CNContact into a readable string with all available details."""
    from Contacts import (  # type: ignore[import-untyped]
        CNContactFormatter,
        CNContactFormatterStyleFullName,
        CNPostalAddressFormatter,
        CNPostalAddressFormatterStyleMailingAddress,
    )

    parts = []

    name = CNContactFormatter.stringFromContact_style_(contact, CNContactFormatterStyleFullName)
    parts.append(f"Name: {name or 'unknown'}")
    parts.append(f"Identifier: {contact.identifier()}")

    org = contact.organizationName()
    if org:
        parts.append(f"Organization: {org}")

    job = contact.jobTitle()
    if job:
        parts.append(f"Job Title: {job}")

    for phone in contact.phoneNumbers():
        label = phone.label() or "other"
        # Strip Apple's internal label prefix
        label = str(label).replace("_$!<", "").replace(">!$_", "")
        parts.append(f"Phone ({label}): {phone.value().stringValue()}")

    for email in contact.emailAddresses():
        label = email.label() or "other"
        label = str(label).replace("_$!<", "").replace(">!$_", "")
        parts.append(f"Email ({label}): {email.value()}")

    for addr in contact.postalAddresses():
        label = addr.label() or "other"
        label = str(label).replace("_$!<", "").replace(">!$_", "")
        formatted = CNPostalAddressFormatter.stringFromPostalAddress_style_(
            addr.value(), CNPostalAddressFormatterStyleMailingAddress
        )
        parts.append(f"Address ({label}): {formatted}")

    for url in contact.urlAddresses():
        label = url.label() or "other"
        label = str(label).replace("_$!<", "").replace(">!$_", "")
        parts.append(f"URL ({label}): {url.value()}")

    bday = contact.birthday()
    if bday:
        month = bday.month()
        day = bday.day()
        year = bday.year()
        if year and year != 7604:  # 7604 = NSDateComponentUndefined
            parts.append(f"Birthday: {year}-{month:02d}-{day:02d}")
        else:
            parts.append(f"Birthday: {month:02d}-{day:02d}")

    try:
        note = contact.note()
        if note:
            parts.append(f"Note: {note}")
    except Exception:
        pass  # note property sometimes not fetchable via enumeration

    return "\n".join(parts)


def _format_contact_brief(contact) -> str:
    """Format a CNContact into a brief one-liner."""
    from Contacts import (  # type: ignore[import-untyped]
        CNContactFormatter,
        CNContactFormatterStyleFullName,
    )

    name = CNContactFormatter.stringFromContact_style_(contact, CNContactFormatterStyleFullName)
    name = str(name) if name else "unknown"

    phones = [p.value().stringValue() for p in contact.phoneNumbers()]
    emails = [str(e.value()) for e in contact.emailAddresses()]
    org = contact.organizationName()

    detail_parts = []
    if org:
        detail_parts.append(str(org))
    if phones:
        detail_parts.append(phones[0])
    if emails:
        detail_parts.append(emails[0])

    detail = " | ".join(detail_parts)
    return f"{name} — {detail}" if detail else name


def search_contacts(query: str, limit: int = 20) -> str:
    """Search contacts by name, phone, or email."""
    _init_store()
    if _store is None:
        return "Error: Contacts access not available."

    try:
        from Contacts import CNContactFetchRequest  # type: ignore[import-untyped]

        keys = _all_keys()
        request = CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)

        all_contacts = []

        def handler(contact, stop):
            all_contacts.append(contact)

        success, error = _store.enumerateContactsWithFetchRequest_error_usingBlock_(
            request, None, handler
        )
        if not success:
            return f"Error fetching contacts: {error}"

        query_lower = query.lower()
        normalized_query = _normalize_phone(query) if "@" not in query else None

        matches = []
        for contact in all_contacts:
            if len(matches) >= limit:
                break

            # Match by name
            given = str(contact.givenName() or "").lower()
            family = str(contact.familyName() or "").lower()
            org = str(contact.organizationName() or "").lower()
            if query_lower in given or query_lower in family or query_lower in org:
                matches.append(contact)
                continue

            full_name = f"{given} {family}"
            if query_lower in full_name:
                matches.append(contact)
                continue

            # Match by phone
            if normalized_query:
                for phone in contact.phoneNumbers():
                    phone_str = phone.value().stringValue()
                    if normalized_query in phone_str or query in phone_str:
                        matches.append(contact)
                        break
                else:
                    # Match by email
                    for email in contact.emailAddresses():
                        if query_lower in str(email.value()).lower():
                            matches.append(contact)
                            break
            else:
                # Query contains @, match by email
                for email in contact.emailAddresses():
                    if query_lower in str(email.value()).lower():
                        matches.append(contact)
                        break

        if not matches:
            return f'No contacts found matching "{query}".'

        return "\n\n".join(_format_contact_brief(c) for c in matches)

    except Exception as e:
        return f"Error searching contacts: {e}"


def get_contact(identifier: str) -> str:
    """Get complete contact record by identifier, name, phone, or email."""
    _init_store()
    if _store is None:
        return "Error: Contacts access not available."

    try:
        from Contacts import CNContactFetchRequest  # type: ignore[import-untyped]

        keys = _all_keys()

        # Try direct identifier lookup first
        try:
            from Foundation import NSArray  # type: ignore[import-untyped]

            ids = NSArray.arrayWithObject_(identifier)
            from Contacts import (  # type: ignore[import-untyped]
                CNContact,
            )

            predicate = CNContact.predicateForContactsWithIdentifiers_(ids)
            contacts, error = _store.unifiedContactsMatchingPredicate_keysToFetch_error_(
                predicate, keys, None
            )
            if contacts and len(contacts) > 0:
                return _format_contact(contacts[0])
        except Exception:
            pass

        # Fall back to enumeration search
        request = CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)
        all_contacts = []

        def handler(contact, stop):
            all_contacts.append(contact)

        success, error = _store.enumerateContactsWithFetchRequest_error_usingBlock_(
            request, None, handler
        )
        if not success:
            return f"Error: {error}"

        query_lower = identifier.lower()
        normalized = _normalize_phone(identifier) if "@" not in identifier else None

        for contact in all_contacts:
            # Name match
            given = str(contact.givenName() or "")
            family = str(contact.familyName() or "")
            full = f"{given} {family}".strip()
            if full.lower() == query_lower or given.lower() == query_lower:
                return _format_contact(contact)

            # Phone match
            if normalized:
                for phone in contact.phoneNumbers():
                    contact_normalized = _normalize_phone(phone.value().stringValue())
                    if contact_normalized == normalized:
                        return _format_contact(contact)

            # Email match
            if "@" in identifier:
                for email in contact.emailAddresses():
                    if str(email.value()).lower() == query_lower:
                        return _format_contact(contact)

        return f"Contact not found: {identifier}"

    except Exception as e:
        return f"Error getting contact: {e}"


def create_contact(
    given_name: str,
    family_name: str = "",
    phones: list[dict[str, str]] | None = None,
    emails: list[dict[str, str]] | None = None,
    organization: str = "",
    job_title: str = "",
    note: str = "",
) -> str:
    """Create a new contact.

    Args:
        given_name: First name
        family_name: Last name
        phones: List of {"label": "mobile", "number": "+15551234567"}
        emails: List of {"label": "home", "address": "foo@bar.com"}
        organization: Company name
        job_title: Job title
        note: Notes field
    """
    _init_store()
    if _store is None:
        return "Error: Contacts access not available."

    try:
        from Contacts import (  # type: ignore[import-untyped]
            CNLabeledValue,
            CNMutableContact,
            CNPhoneNumber,
            CNSaveRequest,
        )
        from Foundation import NSMutableArray  # type: ignore[import-untyped]

        contact = CNMutableContact.alloc().init()
        contact.setGivenName_(given_name)
        if family_name:
            contact.setFamilyName_(family_name)
        if organization:
            contact.setOrganizationName_(organization)
        if job_title:
            contact.setJobTitle_(job_title)
        if note:
            contact.setNote_(note)

        if phones:
            phone_values = NSMutableArray.alloc().init()
            for p in phones:
                label = _label_constant(p.get("label", "mobile"))
                number = CNPhoneNumber.phoneNumberWithStringValue_(p["number"])
                lv = CNLabeledValue.labeledValueWithLabel_value_(label, number)
                phone_values.addObject_(lv)
            contact.setPhoneNumbers_(phone_values)

        if emails:
            email_values = NSMutableArray.alloc().init()
            for e in emails:
                label = _label_constant(e.get("label", "home"))
                lv = CNLabeledValue.labeledValueWithLabel_value_(label, e["address"])
                email_values.addObject_(lv)
            contact.setEmailAddresses_(email_values)

        save_request = CNSaveRequest.alloc().init()
        save_request.addContact_toContainerWithIdentifier_(contact, None)

        success, error = _store.executeSaveRequest_error_(save_request, None)
        if success:
            return f"Created contact: {given_name} {family_name} (ID: {contact.identifier()})"
        return f"Error creating contact: {error}"

    except Exception as e:
        return f"Error creating contact: {e}"


def update_contact(
    identifier: str,
    given_name: str | None = None,
    family_name: str | None = None,
    phones: list[dict[str, str]] | None = None,
    emails: list[dict[str, str]] | None = None,
    organization: str | None = None,
    job_title: str | None = None,
    note: str | None = None,
) -> str:
    """Update an existing contact's fields.

    Args:
        identifier: Contact identifier, name, phone, or email
        given_name: New first name (None to keep existing)
        family_name: New last name (None to keep existing)
        phones: Replace all phones with this list (None to keep existing)
        emails: Replace all emails with this list (None to keep existing)
        organization: New organization (None to keep existing)
        job_title: New job title (None to keep existing)
        note: New note (None to keep existing)
    """
    _init_store()
    if _store is None:
        return "Error: Contacts access not available."

    try:
        from Contacts import (  # type: ignore[import-untyped]
            CNContact,
            CNLabeledValue,
            CNPhoneNumber,
            CNSaveRequest,
        )
        from Foundation import NSArray, NSMutableArray  # type: ignore[import-untyped]

        keys = _all_keys()

        # Find the contact
        mutable = None

        # Try direct identifier
        try:
            ids = NSArray.arrayWithObject_(identifier)
            predicate = CNContact.predicateForContactsWithIdentifiers_(ids)
            contacts, error = _store.unifiedContactsMatchingPredicate_keysToFetch_error_(
                predicate, keys, None
            )
            if contacts and len(contacts) > 0:
                mutable = contacts[0].mutableCopy()
        except Exception:
            pass

        # Fall back to search
        if mutable is None:
            from Contacts import CNContactFetchRequest  # type: ignore[import-untyped]

            request = CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)
            all_contacts = []

            def handler(contact, stop):
                all_contacts.append(contact)

            _store.enumerateContactsWithFetchRequest_error_usingBlock_(request, None, handler)

            query_lower = identifier.lower()
            for contact in all_contacts:
                given = str(contact.givenName() or "")
                family = str(contact.familyName() or "")
                full = f"{given} {family}".strip()
                if full.lower() == query_lower:
                    mutable = contact.mutableCopy()
                    break

        if mutable is None:
            return f"Contact not found: {identifier}"

        # Apply updates
        if given_name is not None:
            mutable.setGivenName_(given_name)
        if family_name is not None:
            mutable.setFamilyName_(family_name)
        if organization is not None:
            mutable.setOrganizationName_(organization)
        if job_title is not None:
            mutable.setJobTitle_(job_title)
        if note is not None:
            mutable.setNote_(note)

        if phones is not None:
            phone_values = NSMutableArray.alloc().init()
            for p in phones:
                label = _label_constant(p.get("label", "mobile"))
                number = CNPhoneNumber.phoneNumberWithStringValue_(p["number"])
                lv = CNLabeledValue.labeledValueWithLabel_value_(label, number)
                phone_values.addObject_(lv)
            mutable.setPhoneNumbers_(phone_values)

        if emails is not None:
            email_values = NSMutableArray.alloc().init()
            for e in emails:
                label = _label_constant(e.get("label", "home"))
                lv = CNLabeledValue.labeledValueWithLabel_value_(label, e["address"])
                email_values.addObject_(lv)
            mutable.setEmailAddresses_(email_values)

        save_request = CNSaveRequest.alloc().init()
        save_request.updateContact_(mutable)

        success, error = _store.executeSaveRequest_error_(save_request, None)
        if success:
            return f"Updated contact: {identifier}"
        return f"Error updating contact: {error}"

    except Exception as e:
        return f"Error updating contact: {e}"


def _label_constant(label: str) -> str:
    """Map common label names to CNLabel constants."""
    mapping = {
        "mobile": "_$!<Mobile>!$_",
        "home": "_$!<Home>!$_",
        "work": "_$!<Work>!$_",
        "main": "_$!<Main>!$_",
        "other": "_$!<Other>!$_",
        "iphone": "iPhone",
    }
    return mapping.get(label.lower(), label)
