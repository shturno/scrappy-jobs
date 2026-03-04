"""Email template engine — renders PT or EN subject and body for a given job."""

from string import Template
from typing import Literal

_PT_SUBJECT = Template("Candidatura para ${job_title} na ${company}")

_PT_BODY = Template("""\
Olá,

Meu nome é ${sender_name} e estou me candidatando para a vaga de ${job_title} na ${company}.

Sou desenvolvedor Full-Stack com experiência em React, Next.js, TypeScript e Python. \
Tenho forte interesse na oportunidade e acredito que meu perfil se alinha bem com os \
requisitos da vaga.

Segue abaixo meu contato e links para avaliação:

• WhatsApp: ${whatsapp_link}
• LinkedIn: ${linkedin_link}
• GitHub: ${github_link}
• Portfólio: ${portfolio}

Fico à disposição para uma conversa. Agradeço a atenção!

Atenciosamente,
${sender_name}
${contact_info}
""")

_EN_SUBJECT = Template("Application for ${job_title} at ${company}")

_EN_BODY = Template("""\
Hello,

My name is ${sender_name} and I am applying for the ${job_title} position at ${company}.

I'm a Full-Stack Developer experienced in React, Next.js, TypeScript, and Python. \
I'm genuinely excited about this opportunity and believe my background is a strong \
match for the role.

Please find my details and links below:

• WhatsApp: ${whatsapp_link}
• LinkedIn: ${linkedin_link}
• GitHub: ${github_link}
• Portfolio: ${portfolio}

I'd love to connect for a conversation. Thank you for your time!

Best regards,
${sender_name}
${contact_info}
""")

_TEMPLATES: dict[str, tuple[Template, Template]] = {
    "pt": (_PT_SUBJECT, _PT_BODY),
    "en": (_EN_SUBJECT, _EN_BODY),
}


def render_template(
    language: Literal["pt", "en"],
    variables: dict[str, str],
) -> tuple[str, str]:
    """Return (subject, body) rendered for the given language.

    Falls back to 'pt' if an unsupported language is passed.
    """
    subject_tpl, body_tpl = _TEMPLATES.get(language, _TEMPLATES["pt"])
    return subject_tpl.substitute(variables), body_tpl.substitute(variables)
