<#import "template.ftl" as layout>
<#-- Sobrescribimos solo la macro del header para cambiar el logo -->
<#macro kcLoginHeader>
    <div id="kc-logo-wrapper" style="text-align: center; padding-bottom: 20px;">
        <img src="${url.resourcesPath}/img/logo.png" alt="OpenPaDi Logo" width="150">
    </div>
</#macro>

<#-- Usamos el layout de registro del tema padre (keycloak o base) -->
<#-- Pasamos las variables necesarias que espera la plantilla padre -->
<#assign
    displayInfo = social.displayInfo!"false",
    displayWide = realm.password && realm.registrationAllowed && !registrationDisabled??
>
<@layout.registrationLayout
    displayMessage=!messagesPerField.existsError('username','password')
    displayInfo=displayInfo
    displayWide=displayWide
    showAnotherWayIfPresent=false
>

    <#-- Sección del Header (aquí se usa nuestra macro personalizada) -->
    <#if section = "header">
        <@kcLoginHeader />
        <#-- El siguiente código es del tema 'base' para mantener el título si existe -->
        <#if !(auth?has_content && auth.showUsername() && !auth.showResetCredentials())>
            <#if displayRequiredFields>
                <div class="${properties.kcContentWrapperClass!}">
                    <div class="${properties.kcLabelWrapperClass!} subtitle">
                        <span class="subtitle"><span class="required">*</span> ${msg("requiredFields")}</span>
                    </div>
                </div>
            </#if>
        <#else>
            <#if displayRequiredFields>
                <div class="${properties.kcContentWrapperClass!}">
                    <div class="${properties.kcLabelWrapperClass!} subtitle">
                        <span class="subtitle"><span class="required">*</span> ${msg("requiredFields")}</span>
                    </div>
                </div>
            </#if>
        </#if>

    <#-- Sección del Formulario (usamos el contenido del formulario del tema padre) -->
    <#elseif section = "form">
        <#if realm.password>
            <div id="kc-form">
                <div id="kc-form-wrapper">
                    <#ifटेज /> <#-- Esto es una directiva de FreeMarker para incluir el contenido del formulario del tema padre -->
                </div>
            </div>
        </#if>

    <#-- Sección de Información (usamos la del tema padre) -->
    <#elseif section = "info" >
        <#if realm.password && realm.registrationAllowed && !registrationDisabled??>
            <div id="kc-registration-container">
                <div id="kc-registration">
                    <span>
                        ${msg("noAccount")} <a tabindex="6" href="${url.registrationUrl}">${msg("doRegister")}</a>
                    </span>
                </div>
            </div>
        </#if>
    </#if>

</@layout.registrationLayout>
