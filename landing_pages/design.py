"""Theme-friendly WordPress blocks for New Neighbors landing pages."""
from django.utils.html import escape


def render_wordpress_content(page, form_url):
    headline = escape(page.headline)
    description = escape(page.description).replace("\n", "<br>")
    button = escape(page.button_text)
    form_url = escape(form_url)
    intro = {
        "valuation": ("Understand your home's next chapter", "Start with a conversation about your property and your goals."),
        "probate": ("Thoughtful support through a property transition", "Get guidance on the next steps for an inherited or estate property."),
        "property_management": ("Practical support for property owners", "Tell us about your property and the support you need."),
        "downsizing": ("A smoother next move", "Discuss timing, priorities, and next steps at your own pace."),
        "open_house": ("Explore your next opportunity", "Connect with our team to learn more."),
        "custom": ("Let's talk about your property", "A conversation is the first step."),
    }
    eyebrow, reassurance = intro.get(page.template, intro["custom"])
    return f"""<!-- wp:group {{"align":"full","style":{{"spacing":{{"padding":{{"top":"64px","bottom":"64px","left":"24px","right":"24px"}}}}}},"backgroundColor":"base"}} -->
<div class="wp-block-group alignfull has-base-background-color has-background" style="padding-top:64px;padding-right:24px;padding-bottom:64px;padding-left:24px">
<!-- wp:group {{"layout":{{"type":"constrained","contentSize":"920px"}}}} -->
<div class="wp-block-group">
<!-- wp:paragraph {{"fontSize":"small"}} --><p class="has-small-font-size">NEW NEIGHBORS · CONNECTICUT &amp; MASSACHUSETTS</p><!-- /wp:paragraph -->
<!-- wp:heading {{"level":1}} --><h1 class="wp-block-heading">{headline}</h1><!-- /wp:heading -->
<!-- wp:paragraph {{"fontSize":"large"}} --><p class="has-large-font-size">{description}</p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="{form_url}">{button}</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:group --></div><!-- /wp:group -->
<!-- wp:group {{"style":{{"spacing":{{"padding":{{"top":"48px","bottom":"48px","left":"24px","right":"24px"}}}}}}}} -->
<div class="wp-block-group" style="padding-top:48px;padding-right:24px;padding-bottom:48px;padding-left:24px">
<!-- wp:group {{"layout":{{"type":"constrained","contentSize":"920px"}}}} --><div class="wp-block-group">
<!-- wp:heading {{"level":2}} --><h2 class="wp-block-heading">{escape(eyebrow)}</h2><!-- /wp:heading -->
<!-- wp:paragraph --><p>{escape(reassurance)}</p><!-- /wp:paragraph -->
<!-- wp:columns -->
<div class="wp-block-columns">
<!-- wp:column --><div class="wp-block-column"><!-- wp:heading {{"level":3}} --><h3 class="wp-block-heading">Tell us what you need</h3><!-- /wp:heading --><!-- wp:paragraph --><p>Share a few details through our secure inquiry form.</p><!-- /wp:paragraph --></div><!-- /wp:column -->
<!-- wp:column --><div class="wp-block-column"><!-- wp:heading {{"level":3}} --><h3 class="wp-block-heading">We review your inquiry</h3><!-- /wp:heading --><!-- wp:paragraph --><p>Our team will review the information you provide.</p><!-- /wp:paragraph --></div><!-- /wp:column -->
<!-- wp:column --><div class="wp-block-column"><!-- wp:heading {{"level":3}} --><h3 class="wp-block-heading">Discuss the next step</h3><!-- /wp:heading --><!-- wp:paragraph --><p>We'll follow up to talk about the right path forward.</p><!-- /wp:paragraph --></div><!-- /wp:column -->
</div><!-- /wp:columns -->
</div><!-- /wp:group --></div><!-- /wp:group -->
<!-- wp:group {{"layout":{{"type":"constrained","contentSize":"920px"}}}} --><div class="wp-block-group"><!-- wp:separator --><hr class="wp-block-separator has-alpha-channel-opacity"/><!-- /wp:separator -->
<!-- wp:paragraph --><p>Serving Connecticut &amp; Massachusetts · Questions? Call <a href="tel:+12034641168">(203) 464-1168</a></p><!-- /wp:paragraph -->
<!-- wp:buttons --><div class="wp-block-buttons"><!-- wp:button --><div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="{form_url}">{button}</a></div><!-- /wp:button --></div><!-- /wp:buttons -->
</div><!-- /wp:group -->"""
