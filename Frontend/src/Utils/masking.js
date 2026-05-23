export const maskEmail = (email = '') => {
    const value = String(email || '').trim();

    if (!value) {
        return '';
    }

    const [localPart, domain = ''] = value.split('@');

    if (!domain) {
        const visibleLength = Math.min(2, value.length);
        return `${value.slice(0, visibleLength)}${'*'.repeat(Math.max(value.length - visibleLength, 0))}`;
    }

    const visibleLocalLength = Math.min(2, localPart.length);
    const maskedLocal = `${localPart.slice(0, visibleLocalLength)}${'*'.repeat(Math.max(localPart.length - visibleLocalLength, 0))}`;
    const [domainName, ...domainRest] = domain.split('.');
    const visibleDomainLength = Math.min(1, domainName.length);
    const maskedDomain = `${domainName.slice(0, visibleDomainLength)}${'*'.repeat(Math.max(domainName.length - visibleDomainLength, 0))}`;

    return `${maskedLocal}@${maskedDomain}${domainRest.length ? `.${domainRest.join('.')}` : ''}`;
};

export const maskLastFiveDigits = (phone = '') => {
    const value = String(phone || '').trim();

    if (!value) {
        return '';
    }

    let maskedDigits = 0;

    return value
        .split('')
        .reverse()
        .map((char) => {
            if (!/\d/.test(char)) {
                return char;
            }

            maskedDigits += 1;
            return maskedDigits <= 5 ? '*' : char;
        })
        .reverse()
        .join('');
};
