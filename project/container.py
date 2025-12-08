"""Dependency Injection Container for EventCally application."""

from dependency_injector import containers, providers

from project import db, repos, services
from project.context import ContextProvider


class Infrastructure(containers.DeclarativeContainer):
    db = providers.Object(db)  # SQLAlchemy database instance


class Context(containers.DeclarativeContainer):
    context_provider = providers.Singleton(ContextProvider)


class Repos(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    api_key_repo = providers.Factory(
        repos.ApiKeyRepo,
        db=infrastructure.db,
    )
    app_installation_repo = providers.Factory(
        repos.AppInstallationRepo,
        db=infrastructure.db,
    )
    app_repo = providers.Factory(
        repos.AppRepo,
        db=infrastructure.db,
    )
    app_key_repo = providers.Factory(
        repos.AppKeyRepo,
        db=infrastructure.db,
    )
    custom_event_category_repo = providers.Factory(
        repos.CustomEventCategoryRepo,
        db=infrastructure.db,
    )
    custom_event_category_set_repo = providers.Factory(
        repos.CustomEventCategorySetRepo,
        db=infrastructure.db,
    )
    custom_widget_repo = providers.Factory(
        repos.CustomWidgetRepo,
        db=infrastructure.db,
    )
    event_category_repo = providers.Factory(
        repos.EventCategoryRepo,
        db=infrastructure.db,
    )
    event_date_repo = providers.Factory(
        repos.EventDateRepo,
        db=infrastructure.db,
    )
    event_date_definition_repo = providers.Factory(
        repos.EventDateDefinitionRepo,
        db=infrastructure.db,
    )
    event_list_repo = providers.Factory(
        repos.EventListRepo,
        db=infrastructure.db,
    )
    event_organizer_repo = providers.Factory(
        repos.EventOrganizerRepo,
        db=infrastructure.db,
    )
    event_place_repo = providers.Factory(
        repos.EventPlaceRepo,
        db=infrastructure.db,
    )
    event_reference_repo = providers.Factory(
        repos.EventReferenceRepo,
        db=infrastructure.db,
    )
    event_reference_request_repo = providers.Factory(
        repos.EventReferenceRequestRepo,
        db=infrastructure.db,
    )
    event_repo = providers.Factory(
        repos.EventRepo,
        db=infrastructure.db,
    )
    image_repo = providers.Factory(
        repos.ImageRepo,
        db=infrastructure.db,
    )
    license_repo = providers.Factory(
        repos.LicenseRepo,
        db=infrastructure.db,
    )
    location_repo = providers.Factory(
        repos.LocationRepo,
        db=infrastructure.db,
    )
    oauth2_authorization_code_repo = providers.Factory(
        repos.OAuth2AuthorizationCodeRepo,
        db=infrastructure.db,
    )
    oauth2_client_repo = providers.Factory(
        repos.OAuth2ClientRepo,
        db=infrastructure.db,
    )
    oauth2_token_repo = providers.Factory(
        repos.OAuth2TokenRepo,
        db=infrastructure.db,
    )
    oauth_repo = providers.Factory(
        repos.OAuthRepo,
        db=infrastructure.db,
    )
    organization_invitation_repo = providers.Factory(
        repos.OrganizationInvitationRepo,
        db=infrastructure.db,
    )
    organization_member_repo = providers.Factory(
        repos.OrganizationMemberRepo,
        db=infrastructure.db,
    )
    organization_member_invitation_repo = providers.Factory(
        repos.OrganizationMemberInvitationRepo,
        db=infrastructure.db,
    )
    organization_member_role_repo = providers.Factory(
        repos.OrganizationMemberRoleRepo,
        db=infrastructure.db,
    )
    organization_relation_repo = providers.Factory(
        repos.OrganizationRelationRepo,
        db=infrastructure.db,
    )
    organization_repo = providers.Factory(
        repos.OrganizationRepo,
        db=infrastructure.db,
    )
    organization_verification_request_repo = providers.Factory(
        repos.OrganizationVerificationRequestRepo,
        db=infrastructure.db,
    )
    role_repo = providers.Factory(
        repos.RoleRepo,
        db=infrastructure.db,
    )
    settings_repo = providers.Factory(
        repos.SettingsRepo,
        db=infrastructure.db,
    )
    user_favorite_events_repo = providers.Factory(
        repos.UserFavoriteEventsRepo,
        db=infrastructure.db,
    )
    user_repo = providers.Factory(
        repos.UserRepo,
        db=infrastructure.db,
    )


class Services(containers.DeclarativeContainer):
    repos = providers.DependenciesContainer()
    context = providers.DependenciesContainer()

    app_service = providers.Factory(
        services.AppService,
        repo=repos.app_repo,
        context_provider=context.context_provider,
        app_key_repo=repos.app_key_repo,
    )
    api_key_service = providers.Factory(
        services.ApiKeyService,
        repo=repos.api_key_repo,
        context_provider=context.context_provider,
    )
    app_installation_service = providers.Factory(
        services.AppInstallationService,
        repo=repos.app_installation_repo,
        context_provider=context.context_provider,
    )
    custom_event_category_service = providers.Factory(
        services.CustomEventCategoryService,
        repo=repos.custom_event_category_repo,
        context_provider=context.context_provider,
    )
    custom_event_category_set_service = providers.Factory(
        services.CustomEventCategorySetService,
        repo=repos.custom_event_category_set_repo,
        context_provider=context.context_provider,
    )
    custom_widget_service = providers.Factory(
        services.CustomWidgetService,
        repo=repos.custom_widget_repo,
        context_provider=context.context_provider,
    )
    event_category_service = providers.Factory(
        services.EventCategoryService,
        repo=repos.event_category_repo,
        context_provider=context.context_provider,
    )
    event_date_service = providers.Factory(
        services.EventDateService,
        repo=repos.event_date_repo,
        context_provider=context.context_provider,
    )
    event_date_definition_service = providers.Factory(
        services.EventDateDefinitionService,
        repo=repos.event_date_definition_repo,
        context_provider=context.context_provider,
    )
    event_list_service = providers.Factory(
        services.EventListService,
        repo=repos.event_list_repo,
        context_provider=context.context_provider,
    )
    event_organizer_service = providers.Factory(
        services.EventOrganizerService,
        repo=repos.event_organizer_repo,
        context_provider=context.context_provider,
    )
    event_place_service = providers.Factory(
        services.EventPlaceService,
        repo=repos.event_place_repo,
        context_provider=context.context_provider,
    )
    event_reference_service = providers.Factory(
        services.EventReferenceService,
        repo=repos.event_reference_repo,
        context_provider=context.context_provider,
    )
    event_reference_request_service = providers.Factory(
        services.EventReferenceRequestService,
        repo=repos.event_reference_request_repo,
        context_provider=context.context_provider,
    )
    event_service = providers.Factory(
        services.EventService,
        repo=repos.event_repo,
        context_provider=context.context_provider,
    )
    image_service = providers.Factory(
        services.ImageService,
        repo=repos.image_repo,
        context_provider=context.context_provider,
    )
    license_service = providers.Factory(
        services.LicenseService,
        repo=repos.license_repo,
        context_provider=context.context_provider,
    )
    location_service = providers.Factory(
        services.LocationService,
        repo=repos.location_repo,
        context_provider=context.context_provider,
    )
    oauth2_authorization_code_service = providers.Factory(
        services.OAuth2AuthorizationCodeService,
        repo=repos.oauth2_authorization_code_repo,
        context_provider=context.context_provider,
    )
    oauth2_client_service = providers.Factory(
        services.OAuth2ClientService,
        repo=repos.oauth2_client_repo,
        context_provider=context.context_provider,
    )
    oauth2_token_service = providers.Factory(
        services.OAuth2TokenService,
        repo=repos.oauth2_token_repo,
        context_provider=context.context_provider,
    )
    oauth_service = providers.Factory(
        services.OAuthService,
        repo=repos.oauth_repo,
        context_provider=context.context_provider,
    )
    organization_invitation_service = providers.Factory(
        services.OrganizationInvitationService,
        repo=repos.organization_invitation_repo,
        context_provider=context.context_provider,
    )
    organization_member_service = providers.Factory(
        services.OrganizationMemberService,
        repo=repos.organization_member_repo,
        context_provider=context.context_provider,
    )
    organization_member_invitation_service = providers.Factory(
        services.OrganizationMemberInvitationService,
        repo=repos.organization_member_invitation_repo,
        context_provider=context.context_provider,
    )
    organization_relation_service = providers.Factory(
        services.OrganizationRelationService,
        repo=repos.organization_relation_repo,
        context_provider=context.context_provider,
    )
    organization_member_role_service = providers.Factory(
        services.OrganizationMemberRoleService,
        repo=repos.organization_member_role_repo,
        context_provider=context.context_provider,
    )
    organization_verification_request_service = providers.Factory(
        services.OrganizationVerificationRequestService,
        repo=repos.organization_verification_request_repo,
        context_provider=context.context_provider,
    )
    organization_service = providers.Factory(
        services.OrganizationService,
        repo=repos.organization_repo,
        context_provider=context.context_provider,
        event_reference_request_service=event_reference_request_service,
        organization_relation_repo=repos.organization_relation_repo,
        event_repo=repos.event_repo,
        event_reference_service=event_reference_service,
        organization_verification_request_service=organization_verification_request_service,
    )
    role_service = providers.Factory(
        services.RoleService,
        repo=repos.role_repo,
        context_provider=context.context_provider,
    )
    settings_service = providers.Factory(
        services.SettingsService,
        repo=repos.settings_repo,
        context_provider=context.context_provider,
    )
    user_favorite_events_service = providers.Factory(
        services.UserFavoriteEventsService,
        repo=repos.user_favorite_events_repo,
        context_provider=context.context_provider,
    )
    user_service = providers.Factory(
        services.UserService,
        repo=repos.user_repo,
        context_provider=context.context_provider,
    )


class Application(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["project.views", "project.api"], warn_unresolved=True
    )

    config = providers.Configuration()

    infrastructure = providers.Container(Infrastructure)
    context = providers.Container(Context)
    repos = providers.Container(
        Repos,
        infrastructure=infrastructure,
    )
    services = providers.Container(
        Services,
        repos=repos,
        context=context,
    )
