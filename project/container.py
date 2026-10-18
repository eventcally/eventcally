"""Dependency Injection Container for EventCally application."""

from dependency_injector import containers, providers
from flask import current_app

from project.application import (
    command_handlers,
    commands,
    event_handlers,
    queries,
    query_handlers,
)
from project.application.message_bus import MessageBus
from project.application.query_bus import QueryBus
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.event_change_summary_service import (
    EventChangeSummaryService,
)
from project.application.services.event_visibility_service import EventVisibilityService
from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)
from project.application.services.webhook_delivery_service import WebhookDeliveryService
from project.application.webhooks.webhook_mapper_context import WebhookMapperContext
from project.domain import events
from project.extensions import db
from project.infrastructure.celery_command_dispatcher import CeleryCommandDispatcher
from project.infrastructure.celery_event_dispatcher import CeleryEventDispatcher
from project.infrastructure.command_handler_factory import CommandHandlerFactory
from project.infrastructure.event_handler_factory import EventHandlerFactory
from project.infrastructure.query_handler_factory import QueryHandlerFactory
from project.infrastructure.read_repositories.sql_alchemy_access_read_repository import (
    SqlAlchemyAccessReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_actor_permission_read_repository import (
    SqlAlchemyActorPermissionReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_api_key_read_repository import (
    SqlAlchemyApiKeyReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_app_child_read_repository import (
    SqlAlchemyAppChildReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_app_installation_read_repository import (
    SqlAlchemyAppInstallationReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_batch_read_repository import (
    SqlAlchemyBatchReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_custom_widget_read_repository import (
    SqlAlchemyCustomWidgetReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_detail_read_repository import (
    SqlAlchemyEventDetailReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_organizer_read_repository import (
    SqlAlchemyEventOrganizerReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_place_read_repository import (
    SqlAlchemyEventPlaceReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_read_repository import (
    SqlAlchemyEventReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_reference_read_repository import (
    SqlAlchemyEventReferenceReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_reference_request_read_repository import (
    SqlAlchemyEventReferenceRequestReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_event_search_read_repository import (
    SqlAlchemyEventSearchReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_image_read_repository import (
    SqlAlchemyImageReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_oauth2_client_read_repository import (
    SqlAlchemyOAuth2ClientReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_oauth2_token_read_repository import (
    SqlAlchemyOAuth2TokenReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_admin_read_repository import (
    SqlAlchemyOrganizationAdminReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_invitation_read_repository import (
    SqlAlchemyOrganizationInvitationReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_member_invitation_read_repository import (
    SqlAlchemyOrganizationMemberInvitationReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_member_read_repository import (
    SqlAlchemyOrganizationMemberReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_read_repository import (
    SqlAlchemyOrganizationReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_relation_read_repository import (
    SqlAlchemyOrganizationRelationReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_organization_verification_request_read_repository import (
    SqlAlchemyOrganizationVerificationRequestReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_reference_data_read_repository import (
    SqlAlchemyReferenceDataReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_reference_request_suggestion_read_repository import (
    SqlAlchemyReferenceRequestSuggestionReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_site_settings_read_repository import (
    SqlAlchemySiteSettingsReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_user_admin_read_repository import (
    SqlAlchemyUserAdminReadRepository,
)
from project.infrastructure.read_repositories.sql_alchemy_webhook_delivery_read_repository import (
    SqlAlchemyWebhookDeliveryReadRepository,
)
from project.infrastructure.read_session import (
    SqlAlchemyReadSessionScope,
    create_read_session,
)
from project.infrastructure.services.app_context_provider import AppContextProvider
from project.infrastructure.services.celery_email_service import CeleryEmailService
from project.infrastructure.services.flask_babel_localization_service import (
    FlaskBabelLocalizationService,
)
from project.infrastructure.services.flask_mail_sender import FlaskMailSender
from project.infrastructure.services.flask_template_render_service import (
    FlaskTemplateRenderService,
)
from project.infrastructure.services.flask_url_provider import FlaskUrlProvider
from project.infrastructure.services.requests_webhook_delivery_sender import (
    RequestsWebhookDeliverySender,
)
from project.infrastructure.services.rsa_app_key_generator import RsaAppKeyGenerator
from project.infrastructure.services.werkzeug_api_key_generator import (
    WerkzeugApiKeyGenerator,
)
from project.infrastructure.services.werkzeug_oauth2_client_credentials_generator import (
    WerkzeugOAuth2ClientCredentialsGenerator,
)
from project.infrastructure.sql_alchemy_unit_of_work import SqlAlchemyUnitOfWork
from project.shared.context import ContextProvider


def get_app_logger():  # pragma: no cover
    return current_app.logger


class Infrastructure(containers.DeclarativeContainer):
    db = providers.Object(db)  # SQLAlchemy database instance
    session_factory = providers.Callable(lambda: db.session)
    # Query side: read-only session, released after every top-level query.
    read_session = providers.Singleton(create_read_session, db=db)
    read_session_scope = providers.Factory(
        SqlAlchemyReadSessionScope,
        read_session=read_session,
    )
    logger = providers.Callable(get_app_logger)
    localization_service = providers.Singleton(
        FlaskBabelLocalizationService,
    )
    template_render_service = providers.Singleton(
        FlaskTemplateRenderService,
    )
    url_provider = providers.Singleton(
        FlaskUrlProvider,
    )
    mail_sender = providers.Singleton(
        FlaskMailSender,
    )
    webhook_delivery_sender = providers.Singleton(
        RequestsWebhookDeliverySender,
        logger=logger,
        url_provider=url_provider,
    )
    api_key_generator = providers.Singleton(
        WerkzeugApiKeyGenerator,
    )
    app_key_generator = providers.Singleton(
        RsaAppKeyGenerator,
    )
    oauth2_client_credentials_generator = providers.Singleton(
        WerkzeugOAuth2ClientCredentialsGenerator,
    )


class Context(containers.DeclarativeContainer):
    context_provider = providers.Singleton(ContextProvider)
    app_context_provider = providers.Singleton(
        AppContextProvider, context_provider=context_provider
    )


class ReadRepos(containers.DeclarativeContainer):
    infrastructure = providers.DependenciesContainer()

    # Event-handler read repos run inside the handler's unit of work and stay on
    # session_factory. Read repos for query handlers use infrastructure.read_session.

    event_read_repo = providers.Factory(
        SqlAlchemyEventReadRepository,
        session=infrastructure.session_factory,
    )
    webhook_delivery_read_repo = providers.Factory(
        SqlAlchemyWebhookDeliveryReadRepository,
        session=infrastructure.session_factory,
    )
    uow_access_read_repo = providers.Factory(
        SqlAlchemyAccessReadRepository,
        session=infrastructure.session_factory,
    )

    event_organizer_read_repo = providers.Factory(
        SqlAlchemyEventOrganizerReadRepository,
        session=infrastructure.read_session,
    )
    event_place_read_repo = providers.Factory(
        SqlAlchemyEventPlaceReadRepository,
        session=infrastructure.read_session,
    )
    user_admin_read_repo = providers.Factory(
        SqlAlchemyUserAdminReadRepository,
        session=infrastructure.read_session,
    )
    access_read_repo = providers.Factory(
        SqlAlchemyAccessReadRepository,
        session=infrastructure.read_session,
    )
    site_settings_read_repo = providers.Factory(
        SqlAlchemySiteSettingsReadRepository,
        session=infrastructure.read_session,
    )
    batch_read_repo = providers.Factory(
        SqlAlchemyBatchReadRepository,
        session=infrastructure.read_session,
    )
    image_read_repo = providers.Factory(
        SqlAlchemyImageReadRepository,
        session=infrastructure.read_session,
    )
    event_search_read_repo = providers.Factory(
        SqlAlchemyEventSearchReadRepository,
        session=infrastructure.read_session,
    )
    event_detail_read_repo = providers.Factory(
        SqlAlchemyEventDetailReadRepository,
        session=infrastructure.read_session,
    )
    actor_permission_read_repo = providers.Factory(
        SqlAlchemyActorPermissionReadRepository,
        session=infrastructure.read_session,
    )
    organization_invitation_read_repo = providers.Factory(
        SqlAlchemyOrganizationInvitationReadRepository,
        session=infrastructure.read_session,
    )
    organization_member_read_repo = providers.Factory(
        SqlAlchemyOrganizationMemberReadRepository,
        session=infrastructure.read_session,
    )

    organization_member_invitation_read_repo = providers.Factory(
        SqlAlchemyOrganizationMemberInvitationReadRepository,
        session=infrastructure.read_session,
    )

    api_key_read_repo = providers.Factory(
        SqlAlchemyApiKeyReadRepository,
        session=infrastructure.read_session,
    )

    oauth2_client_read_repo = providers.Factory(
        SqlAlchemyOAuth2ClientReadRepository,
        session=infrastructure.read_session,
    )

    app_child_read_repo = providers.Factory(
        SqlAlchemyAppChildReadRepository,
        session=infrastructure.read_session,
    )

    app_installation_read_repo = providers.Factory(
        SqlAlchemyAppInstallationReadRepository,
        session=infrastructure.read_session,
    )

    oauth2_token_read_repo = providers.Factory(
        SqlAlchemyOAuth2TokenReadRepository,
        session=infrastructure.read_session,
    )

    event_reference_read_repo = providers.Factory(
        SqlAlchemyEventReferenceReadRepository,
        session=infrastructure.read_session,
    )

    event_reference_request_read_repo = providers.Factory(
        SqlAlchemyEventReferenceRequestReadRepository,
        session=infrastructure.read_session,
    )

    organization_verification_request_read_repo = providers.Factory(
        SqlAlchemyOrganizationVerificationRequestReadRepository,
        session=infrastructure.read_session,
    )

    reference_request_suggestion_read_repo = providers.Factory(
        SqlAlchemyReferenceRequestSuggestionReadRepository,
        session=infrastructure.read_session,
    )

    organization_relation_read_repo = providers.Factory(
        SqlAlchemyOrganizationRelationReadRepository,
        session=infrastructure.read_session,
    )

    organization_admin_read_repo = providers.Factory(
        SqlAlchemyOrganizationAdminReadRepository,
        session=infrastructure.read_session,
    )

    organization_read_repo = providers.Factory(
        SqlAlchemyOrganizationReadRepository,
        session=infrastructure.read_session,
    )

    custom_widget_read_repo = providers.Factory(
        SqlAlchemyCustomWidgetReadRepository,
        session=infrastructure.read_session,
    )

    reference_data_read_repo = providers.Factory(
        SqlAlchemyReferenceDataReadRepository,
        session=infrastructure.read_session,
    )


class Services(containers.DeclarativeContainer):
    read_repos = providers.DependenciesContainer()
    config = providers.Configuration()
    infrastructure = providers.DependenciesContainer()

    email_service = providers.Factory(
        CeleryEmailService,
        default_locale=config.BABEL_DEFAULT_LOCALE,
        localization_service=infrastructure.localization_service,
        template_render_service=infrastructure.template_render_service,
        mail_sender=infrastructure.mail_sender,
    )
    webhook_delivery_service = providers.Factory(
        WebhookDeliveryService,
        logger=infrastructure.logger,
        webhook_delivery_sender=infrastructure.webhook_delivery_sender,
        webhook_delivery_read_repo=read_repos.webhook_delivery_read_repo,
    )
    organization_application_service = providers.Factory(
        OrganizationApplicationService,
        email_service=email_service,
    )
    event_change_summary_service = providers.Factory(
        EventChangeSummaryService,
        event_read_repo=read_repos.event_read_repo,
    )


class Cqrs(containers.DeclarativeContainer):
    __self__ = providers.Self()
    infrastructure = providers.DependenciesContainer()
    context = providers.DependenciesContainer()
    services = providers.DependenciesContainer()
    read_repos = providers.DependenciesContainer()
    config = providers.Configuration()

    uow = providers.Factory(
        SqlAlchemyUnitOfWork,
        scoped_session_or_factory=infrastructure.session_factory,
    )

    webhook_mapper_context = providers.Singleton(
        WebhookMapperContext,
        url_provider=infrastructure.url_provider,
    )

    command_handler_factory = providers.Singleton(
        CommandHandlerFactory,
        factory_aggregate=providers.FactoryAggregate(
            {
                commands.CreateEventCommand: providers.Factory(
                    command_handlers.CreateEventHandler
                ),
                commands.UpdateEventCommand: providers.Factory(
                    command_handlers.UpdateEventHandler
                ),
                commands.UpdateEventRecurringDatesCommand: providers.Factory(
                    command_handlers.UpdateEventRecurringDatesHandler
                ),
                commands.DeleteEventCommand: providers.Factory(
                    command_handlers.DeleteEventHandler
                ),
                commands.CreateEventOrganizerCommand: providers.Factory(
                    command_handlers.CreateEventOrganizerHandler
                ),
                commands.UpdateEventOrganizerCommand: providers.Factory(
                    command_handlers.UpdateEventOrganizerHandler
                ),
                commands.DeleteEventOrganizerCommand: providers.Factory(
                    command_handlers.DeleteEventOrganizerHandler
                ),
                commands.CreateEventPlaceCommand: providers.Factory(
                    command_handlers.CreateEventPlaceHandler
                ),
                commands.UpdateEventPlaceCommand: providers.Factory(
                    command_handlers.UpdateEventPlaceHandler
                ),
                commands.DeleteEventPlaceCommand: providers.Factory(
                    command_handlers.DeleteEventPlaceHandler
                ),
                commands.CreateEventReferenceCommand: providers.Factory(
                    command_handlers.CreateEventReferenceHandler
                ),
                commands.UpdateEventReferenceCommand: providers.Factory(
                    command_handlers.UpdateEventReferenceHandler
                ),
                commands.DeleteEventReferenceCommand: providers.Factory(
                    command_handlers.DeleteEventReferenceHandler
                ),
                commands.RequestEventReferenceCommand: providers.Factory(
                    command_handlers.RequestEventReferenceHandler
                ),
                commands.VerifyEventReferenceRequestCommand: providers.Factory(
                    command_handlers.VerifyEventReferenceRequestHandler
                ),
                commands.RejectEventReferenceRequestCommand: providers.Factory(
                    command_handlers.RejectEventReferenceRequestHandler
                ),
                commands.WithdrawEventReferenceRequestCommand: providers.Factory(
                    command_handlers.WithdrawEventReferenceRequestHandler
                ),
                commands.CreateCustomWidgetCommand: providers.Factory(
                    command_handlers.CreateCustomWidgetHandler
                ),
                commands.UpdateCustomWidgetCommand: providers.Factory(
                    command_handlers.UpdateCustomWidgetHandler
                ),
                commands.DeleteCustomWidgetCommand: providers.Factory(
                    command_handlers.DeleteCustomWidgetHandler
                ),
                commands.CreateOrganizationCommand: providers.Factory(
                    command_handlers.CreateOrganizationHandler
                ),
                commands.UpdateOrganizationCommand: providers.Factory(
                    command_handlers.UpdateOrganizationHandler
                ),
                commands.UpdateOrganizationWidgetSettingsCommand: providers.Factory(
                    command_handlers.UpdateOrganizationWidgetSettingsHandler
                ),
                commands.UpdateOrganizationAdminSettingsCommand: providers.Factory(
                    command_handlers.UpdateOrganizationAdminSettingsHandler
                ),
                commands.CreateOrganizationRelationCommand: providers.Factory(
                    command_handlers.CreateOrganizationRelationHandler
                ),
                commands.UpdateOrganizationRelationCommand: providers.Factory(
                    command_handlers.UpdateOrganizationRelationHandler
                ),
                commands.DeleteOrganizationRelationCommand: providers.Factory(
                    command_handlers.DeleteOrganizationRelationHandler
                ),
                commands.RequestOrganizationVerificationCommand: providers.Factory(
                    command_handlers.RequestOrganizationVerificationHandler
                ),
                commands.VerifyOrganizationCommand: providers.Factory(
                    command_handlers.VerifyOrganizationHandler
                ),
                commands.ApproveOrganizationVerificationRequestCommand: providers.Factory(
                    command_handlers.ApproveOrganizationVerificationRequestHandler
                ),
                commands.RejectOrganizationVerificationRequestCommand: providers.Factory(
                    command_handlers.RejectOrganizationVerificationRequestHandler
                ),
                commands.WithdrawOrganizationVerificationRequestCommand: providers.Factory(
                    command_handlers.WithdrawOrganizationVerificationRequestHandler
                ),
                commands.DeleteOldWebhookEventsCommand: providers.Factory(
                    command_handlers.DeleteOldWebhookEventsHandler
                ),
                commands.DeleteOrganizationDueForDeletionCommand: providers.Factory(
                    command_handlers.DeleteOrganizationDueForDeletionHandler
                ),
                commands.DeleteUserDueForDeletionCommand: providers.Factory(
                    command_handlers.DeleteUserDueForDeletionHandler
                ),
                commands.DeleteGhostUserCommand: providers.Factory(
                    command_handlers.DeleteGhostUserHandler
                ),
                commands.DeleteOldEventCommand: providers.Factory(
                    command_handlers.DeleteOldEventHandler
                ),
                commands.RequestOrganizationDeletionCommand: providers.Factory(
                    command_handlers.RequestOrganizationDeletionHandler
                ),
                commands.CancelOrganizationDeletionCommand: providers.Factory(
                    command_handlers.CancelOrganizationDeletionHandler
                ),
                commands.DeleteOrganizationCommand: providers.Factory(
                    command_handlers.DeleteOrganizationHandler
                ),
                commands.RequestUserDeletionCommand: providers.Factory(
                    command_handlers.RequestUserDeletionHandler
                ),
                commands.CancelUserDeletionCommand: providers.Factory(
                    command_handlers.CancelUserDeletionHandler
                ),
                commands.AcceptTosCommand: providers.Factory(
                    command_handlers.AcceptTosHandler
                ),
                commands.UpdateUserGeneralSettingsCommand: providers.Factory(
                    command_handlers.UpdateUserGeneralSettingsHandler
                ),
                commands.UpdateUserNotificationSettingsCommand: providers.Factory(
                    command_handlers.UpdateUserNotificationSettingsHandler
                ),
                commands.UpdateUserRolesCommand: providers.Factory(
                    command_handlers.UpdateUserRolesHandler
                ),
                commands.DeleteUserCommand: providers.Factory(
                    command_handlers.DeleteUserHandler
                ),
                commands.ResetTosAcceptedForUsersCommand: providers.Factory(
                    command_handlers.ResetTosAcceptedForUsersHandler
                ),
                commands.UpdateSettingsCommand: providers.Factory(
                    command_handlers.UpdateSettingsHandler
                ),
                commands.UpdatePlanningSettingsCommand: providers.Factory(
                    command_handlers.UpdatePlanningSettingsHandler
                ),
                commands.CreateApiKeyCommand: providers.Factory(
                    command_handlers.CreateApiKeyHandler,
                    api_key_generator=infrastructure.api_key_generator,
                ),
                commands.UpdateApiKeyCommand: providers.Factory(
                    command_handlers.UpdateApiKeyHandler
                ),
                commands.DeleteApiKeyCommand: providers.Factory(
                    command_handlers.DeleteApiKeyHandler
                ),
                commands.CreateAppCommand: providers.Factory(
                    command_handlers.CreateAppHandler,
                    credentials_generator=infrastructure.oauth2_client_credentials_generator,
                ),
                commands.UpdateAppCommand: providers.Factory(
                    command_handlers.UpdateAppHandler
                ),
                commands.UpdateAppInstallationPermissionsCommand: providers.Factory(
                    command_handlers.UpdateAppInstallationPermissionsHandler
                ),
                commands.UninstallAppCommand: providers.Factory(
                    command_handlers.UninstallAppHandler
                ),
                commands.DeleteAppCommand: providers.Factory(
                    command_handlers.DeleteAppHandler
                ),
                commands.InstallAppCommand: providers.Factory(
                    command_handlers.InstallAppHandler
                ),
                commands.CreateAppKeyCommand: providers.Factory(
                    command_handlers.CreateAppKeyHandler,
                    app_key_generator=infrastructure.app_key_generator,
                ),
                commands.DeleteAppKeyCommand: providers.Factory(
                    command_handlers.DeleteAppKeyHandler
                ),
                commands.CreateOAuth2ClientCommand: providers.Factory(
                    command_handlers.CreateOAuth2ClientHandler,
                    credentials_generator=infrastructure.oauth2_client_credentials_generator,
                ),
                commands.UpdateOAuth2ClientCommand: providers.Factory(
                    command_handlers.UpdateOAuth2ClientHandler
                ),
                commands.DeleteOAuth2ClientCommand: providers.Factory(
                    command_handlers.DeleteOAuth2ClientHandler
                ),
                commands.RevokeOAuth2TokenCommand: providers.Factory(
                    command_handlers.RevokeOAuth2TokenHandler
                ),
                commands.AttemptToDeliverWebhookCommand: providers.Factory(
                    command_handlers.AttemptToDeliverWebhookHandler,
                    webhook_delivery_service=services.webhook_delivery_service,
                ),
                commands.ReportEventCommand: providers.Factory(
                    command_handlers.ReportEventHandler,
                    access_read_repo=read_repos.uow_access_read_repo,
                    email_service=services.email_service,
                ),
                commands.InviteOrganizationCommand: providers.Factory(
                    command_handlers.InviteOrganizationHandler
                ),
                commands.UpdateOrganizationInvitationCommand: providers.Factory(
                    command_handlers.UpdateOrganizationInvitationHandler
                ),
                commands.RevokeOrganizationInvitationCommand: providers.Factory(
                    command_handlers.RevokeOrganizationInvitationHandler
                ),
                commands.DeclineOrganizationInvitationCommand: providers.Factory(
                    command_handlers.DeclineOrganizationInvitationHandler
                ),
                commands.InviteUserToOrganizationCommand: providers.Factory(
                    command_handlers.InviteUserToOrganizationHandler
                ),
                commands.UpdateMemberInvitationCommand: providers.Factory(
                    command_handlers.UpdateMemberInvitationHandler
                ),
                commands.RevokeMemberInvitationCommand: providers.Factory(
                    command_handlers.RevokeMemberInvitationHandler
                ),
                commands.AcceptMemberInvitationCommand: providers.Factory(
                    command_handlers.AcceptMemberInvitationHandler
                ),
                commands.DeclineMemberInvitationCommand: providers.Factory(
                    command_handlers.DeclineMemberInvitationHandler
                ),
                commands.ChangeOrganizationMemberRolesCommand: providers.Factory(
                    command_handlers.ChangeOrganizationMemberRolesHandler
                ),
                commands.RemoveOrganizationMemberCommand: providers.Factory(
                    command_handlers.RemoveOrganizationMemberHandler
                ),
                commands.LeaveOrganizationCommand: providers.Factory(
                    command_handlers.LeaveOrganizationHandler
                ),
            }
        ),
    )

    event_handler_factory = providers.Singleton(
        EventHandlerFactory,
        factory_aggregate=providers.FactoryAggregate(
            {
                events.WebhookDeliveryCreated: providers.List(
                    providers.Factory(
                        event_handlers.WebhookDeliveryCreatedAttemptEventHandler,
                        webhook_delivery_service=services.webhook_delivery_service,
                    ),
                ),
                events.EventCreated: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventUpdated: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                    providers.Factory(
                        event_handlers.ReferenceEventChangedEmailEventHandler,
                        organization_service=services.organization_application_service,
                        event_read_repo=read_repos.event_read_repo,
                        change_summary_service=services.event_change_summary_service,
                        details_enabled=config.FEATURE_REFERENCED_EVENT_CHANGED_DETAILS_ENABLED,
                    ),
                ),
                events.EventDeleted: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventOrganizerCreated: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventOrganizerUpdated: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventOrganizerDeleted: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventPlaceCreated: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventPlaceUpdated: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.EventPlaceDeleted: providers.List(
                    providers.Factory(
                        event_handlers.AppInstallationWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.AppInstallationCreated: providers.List(
                    providers.Factory(
                        event_handlers.AppWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.AppInstallationPermissionsUpdated: providers.List(
                    providers.Factory(
                        event_handlers.AppWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.AppInstallationDeleted: providers.List(
                    providers.Factory(
                        event_handlers.AppWebhookEventHandler,
                        mapper_context=webhook_mapper_context,
                    ),
                ),
                events.OrganizationDeletionRequested: providers.List(
                    providers.Factory(
                        event_handlers.OrganizationDeletionRequestedEmailEventHandler,
                        organization_service=services.organization_application_service,
                    )
                ),
                events.OrganizationVerificationRequested: providers.List(
                    providers.Factory(
                        event_handlers.OrganizationVerificationRequestedEmailEventHandler,
                        organization_service=services.organization_application_service,
                    )
                ),
                events.OrganizationVerificationRequestReviewed: providers.List(
                    providers.Factory(
                        event_handlers.OrganizationVerificationRequestReviewedEmailEventHandler,
                        organization_service=services.organization_application_service,
                    )
                ),
                events.OrganizationInvitationCreated: providers.List(
                    providers.Factory(
                        event_handlers.OrganizationInvitationCreatedEmailEventHandler,
                        email_service=services.email_service,
                    )
                ),
                events.UserDeletionRequested: providers.List(
                    providers.Factory(
                        event_handlers.UserDeletionRequestedEmailEventHandler,
                        email_service=services.email_service,
                    )
                ),
                events.OrganizationInvitationAccepted: providers.List(
                    providers.Factory(
                        event_handlers.OrganizationInvitationAcceptedEmailEventHandler,
                        organization_service=services.organization_application_service,
                    )
                ),
                events.MemberInvitationCreated: providers.List(
                    providers.Factory(
                        event_handlers.MemberInvitationCreatedEmailEventHandler,
                        email_service=services.email_service,
                    )
                ),
                events.EventReferenceRequestCreated: providers.List(
                    providers.Factory(
                        event_handlers.EventReferenceRequestCreatedEmailEventHandler,
                        organization_service=services.organization_application_service,
                        event_read_repo=read_repos.event_read_repo,
                    )
                ),
                events.EventReferenceRequestAutoVerified: providers.List(
                    providers.Factory(
                        event_handlers.EventReferenceRequestAutoVerifiedEmailEventHandler,
                        organization_service=services.organization_application_service,
                        event_read_repo=read_repos.event_read_repo,
                    )
                ),
                events.EventReferenceRequestReviewed: providers.List(
                    providers.Factory(
                        event_handlers.EventReferenceRequestReviewedEmailEventHandler,
                        organization_service=services.organization_application_service,
                    )
                ),
            }
        ),
    )

    event_dispatcher = providers.Factory(CeleryEventDispatcher)
    command_dispatcher = providers.Factory(CeleryCommandDispatcher)

    message_bus = providers.Factory(
        MessageBus,
        uow_factory=__self__,
        app_context_provider=context.app_context_provider,
        command_handler_factory=command_handler_factory,
        event_handler_factory=event_handler_factory,
        event_dispatcher=event_dispatcher,
        command_dispatcher=command_dispatcher,
    )

    actor_authorization_service = providers.Factory(
        ActorAuthorizationService,
        reader=read_repos.actor_permission_read_repo,
    )

    event_visibility_service = providers.Factory(
        EventVisibilityService,
        authz=actor_authorization_service,
    )

    query_handler_factory = providers.Singleton(
        QueryHandlerFactory,
        factory_aggregate=providers.FactoryAggregate(
            {
                queries.ListEventOrganizersQuery: providers.Factory(
                    query_handlers.ListEventOrganizersHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
                queries.GetEventOrganizerQuery: providers.Factory(
                    query_handlers.GetEventOrganizerHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
                queries.GetEventOrganizerForEditQuery: providers.Factory(
                    query_handlers.GetEventOrganizerForEditHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
                queries.IsEventOrganizerNameTakenQuery: providers.Factory(
                    query_handlers.IsEventOrganizerNameTakenHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
                queries.ListEventPlacesQuery: providers.Factory(
                    query_handlers.ListEventPlacesHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                queries.GetEventPlaceQuery: providers.Factory(
                    query_handlers.GetEventPlaceHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                queries.GetEventPlaceForEditQuery: providers.Factory(
                    query_handlers.GetEventPlaceForEditHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                queries.IsEventPlaceNameTakenQuery: providers.Factory(
                    query_handlers.IsEventPlaceNameTakenHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                queries.ListEventPlaceSuggestionsQuery: providers.Factory(
                    query_handlers.ListEventPlaceSuggestionsHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                # S7 entries
                queries.LookupLicensesQuery: providers.Factory(
                    query_handlers.LookupLicensesHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.GetLicenseQuery: providers.Factory(
                    query_handlers.GetLicenseHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.ListAllEventCategoriesQuery: providers.Factory(
                    query_handlers.ListAllEventCategoriesHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.GetEventCategoryByNameQuery: providers.Factory(
                    query_handlers.GetEventCategoryByNameHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.GetEventCategoryQuery: providers.Factory(
                    query_handlers.GetEventCategoryHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.LookupCustomEventCategoriesQuery: providers.Factory(
                    query_handlers.LookupCustomEventCategoriesHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.GetCustomEventCategoryQuery: providers.Factory(
                    query_handlers.GetCustomEventCategoryHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.LookupEventOrganizersQuery: providers.Factory(
                    query_handlers.LookupEventOrganizersHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
                queries.GetEventOrganizerRefQuery: providers.Factory(
                    query_handlers.GetEventOrganizerRefHandler,
                    repo=read_repos.event_organizer_read_repo,
                ),
                queries.LookupEventPlacesQuery: providers.Factory(
                    query_handlers.LookupEventPlacesHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                queries.GetEventPlaceRefQuery: providers.Factory(
                    query_handlers.GetEventPlaceRefHandler,
                    repo=read_repos.event_place_read_repo,
                ),
                # S8 entries
                queries.SearchEventDatesQuery: providers.Factory(
                    query_handlers.SearchEventDatesHandler,
                    repo=read_repos.event_search_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.SearchEventsQuery: providers.Factory(
                    query_handlers.SearchEventsHandler,
                    repo=read_repos.event_search_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.ListEventsQuery: providers.Factory(
                    query_handlers.ListEventsHandler,
                    repo=read_repos.event_search_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.ListAllEventsQuery: providers.Factory(
                    query_handlers.ListAllEventsHandler,
                    repo=read_repos.event_search_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.ListEventDatesQuery: providers.Factory(
                    query_handlers.ListEventDatesHandler,
                    repo=read_repos.event_search_read_repo,
                ),
                queries.GetEventDetailQuery: providers.Factory(
                    query_handlers.GetEventDetailHandler,
                    repo=read_repos.event_detail_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.GetEventForEditQuery: providers.Factory(
                    query_handlers.GetEventForEditHandler,
                    repo=read_repos.event_detail_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.EventExistsQuery: providers.Factory(
                    query_handlers.EventExistsHandler,
                    repo=read_repos.event_detail_read_repo,
                ),
                queries.GetEventDateDetailQuery: providers.Factory(
                    query_handlers.GetEventDateDetailHandler,
                    repo=read_repos.event_detail_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.ListEventDatesOfEventQuery: providers.Factory(
                    query_handlers.ListEventDatesOfEventHandler,
                    repo=read_repos.event_detail_read_repo,
                    visibility=event_visibility_service,
                ),
                queries.ListUpcomingEventDatesQuery: providers.Factory(
                    query_handlers.ListUpcomingEventDatesHandler,
                    repo=read_repos.event_detail_read_repo,
                ),
                # S9 entries
                queries.ListDumpEventsQuery: providers.Factory(
                    query_handlers.ListDumpEventsHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListDumpPlacesQuery: providers.Factory(
                    query_handlers.ListDumpPlacesHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListDumpOrganizersQuery: providers.Factory(
                    query_handlers.ListDumpOrganizersHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListDumpOrganizationsQuery: providers.Factory(
                    query_handlers.ListDumpOrganizationsHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListDumpEventCategoriesQuery: providers.Factory(
                    query_handlers.ListDumpEventCategoriesHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListDumpEventReferencesQuery: providers.Factory(
                    query_handlers.ListDumpEventReferencesHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListSitemapEventsQuery: providers.Factory(
                    query_handlers.ListSitemapEventsHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListOrganizationIdsDueForDeletionQuery: providers.Factory(
                    query_handlers.ListOrganizationIdsDueForDeletionHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListUserIdsDueForDeletionQuery: providers.Factory(
                    query_handlers.ListUserIdsDueForDeletionHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListGhostUserIdsQuery: providers.Factory(
                    query_handlers.ListGhostUserIdsHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListRecurringEventIdsQuery: providers.Factory(
                    query_handlers.ListRecurringEventIdsHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.ListOldEventIdsQuery: providers.Factory(
                    query_handlers.ListOldEventIdsHandler,
                    repo=read_repos.batch_read_repo,
                ),
                queries.GetImageMetaQuery: providers.Factory(
                    query_handlers.GetImageMetaHandler,
                    repo=read_repos.image_read_repo,
                ),
                queries.GetImageFileQuery: providers.Factory(
                    query_handlers.GetImageFileHandler,
                    repo=read_repos.image_read_repo,
                ),
                # S10 entries
                queries.GetCurrentOrganizationQuery: providers.Factory(
                    query_handlers.GetCurrentOrganizationHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.GetResourceOwnerQuery: providers.Factory(
                    query_handlers.GetResourceOwnerHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.HasOtherAdminQuery: providers.Factory(
                    query_handlers.HasOtherAdminHandler,
                    repo=read_repos.access_read_repo,
                ),
                # Jinja/access helper entries
                queries.GetManageMenuOptionsQuery: providers.Factory(
                    query_handlers.GetManageMenuOptionsHandler,
                    repo=read_repos.access_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetCurrentMemberGrantsQuery: providers.Factory(
                    query_handlers.GetCurrentMemberGrantsHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.GetSettingsQuery: providers.Factory(
                    query_handlers.GetSettingsHandler,
                    repo=read_repos.site_settings_read_repo,
                ),
                queries.GetSiteNoticesQuery: providers.Factory(
                    query_handlers.GetSiteNoticesHandler,
                    repo=read_repos.site_settings_read_repo,
                ),
                queries.GetApiKeyByHashQuery: providers.Factory(
                    query_handlers.GetApiKeyByHashHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.IsOrganizationNameTakenQuery: providers.Factory(
                    query_handlers.IsOrganizationNameTakenHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.IsOrganizationShortNameTakenQuery: providers.Factory(
                    query_handlers.IsOrganizationShortNameTakenHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.CanRequestVerificationQuery: providers.Factory(
                    query_handlers.CanRequestVerificationHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.AnyOrganizationAcceptsReferenceRequestsQuery: providers.Factory(
                    query_handlers.AnyOrganizationAcceptsReferenceRequestsHandler,
                    repo=read_repos.access_read_repo,
                ),
                queries.GetOrganizationSettingsQuery: providers.Factory(
                    query_handlers.GetOrganizationSettingsHandler,
                    repo=read_repos.access_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetManageableOrganizationQuery: providers.Factory(
                    query_handlers.GetManageableOrganizationHandler,
                    repo=read_repos.access_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUsersForAdminQuery: providers.Factory(
                    query_handlers.ListUsersForAdminHandler,
                    repo=read_repos.user_admin_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetUserForAdminQuery: providers.Factory(
                    query_handlers.GetUserForAdminHandler,
                    repo=read_repos.user_admin_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListRolesQuery: providers.Factory(
                    query_handlers.ListRolesHandler,
                    repo=read_repos.user_admin_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListNewsletterRecipientsQuery: providers.Factory(
                    query_handlers.ListNewsletterRecipientsHandler,
                    repo=read_repos.user_admin_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListManageableOrganizationsQuery: providers.Factory(
                    query_handlers.ListManageableOrganizationsHandler,
                    repo=read_repos.access_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListReferenceRequestSuggestionsQuery: providers.Factory(
                    query_handlers.ListReferenceRequestSuggestionsHandler,
                    repo=read_repos.reference_request_suggestion_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOrganizationInvitationsQuery: providers.Factory(
                    query_handlers.ListOrganizationInvitationsHandler,
                    repo=read_repos.organization_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOrganizationInvitationQuery: providers.Factory(
                    query_handlers.GetOrganizationInvitationHandler,
                    repo=read_repos.organization_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                # S5 entries
                queries.GetIncomingOrganizationVerificationRequestReviewQuery: providers.Factory(
                    query_handlers.GetIncomingOrganizationVerificationRequestReviewHandler,
                    repo=read_repos.organization_verification_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListLicensesQuery: providers.Factory(
                    query_handlers.ListLicensesHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.ListEventCategoriesQuery: providers.Factory(
                    query_handlers.ListEventCategoriesHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.ListCustomEventCategorySetsQuery: providers.Factory(
                    query_handlers.ListCustomEventCategorySetsHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.ListCustomEventCategoriesQuery: providers.Factory(
                    query_handlers.ListCustomEventCategoriesHandler,
                    repo=read_repos.reference_data_read_repo,
                ),
                queries.ListCustomWidgetsQuery: providers.Factory(
                    query_handlers.ListCustomWidgetsHandler,
                    repo=read_repos.custom_widget_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetCustomWidgetQuery: providers.Factory(
                    query_handlers.GetCustomWidgetHandler,
                    repo=read_repos.custom_widget_read_repo,
                ),
                queries.SearchOrganizationsQuery: providers.Factory(
                    query_handlers.SearchOrganizationsHandler,
                    repo=read_repos.organization_read_repo,
                ),
                queries.GetOrganizationWidgetSettingsQuery: providers.Factory(
                    query_handlers.GetOrganizationWidgetSettingsHandler,
                    repo=read_repos.organization_read_repo,
                ),
                queries.ListVerifierOrganizationsQuery: providers.Factory(
                    query_handlers.ListVerifierOrganizationsHandler,
                    repo=read_repos.organization_read_repo,
                ),
                queries.GetOrganizationQuery: providers.Factory(
                    query_handlers.GetOrganizationHandler,
                    repo=read_repos.organization_read_repo,
                ),
                queries.ListWebhookDeliveriesForAppQuery: providers.Factory(
                    query_handlers.ListWebhookDeliveriesForAppHandler,
                    repo=read_repos.app_child_read_repo,
                ),
                queries.GetWebhookDeliveryForAppQuery: providers.Factory(
                    query_handlers.GetWebhookDeliveryForAppHandler,
                    repo=read_repos.app_child_read_repo,
                ),
                queries.ListWebhookDeliveryAttemptsForAppQuery: providers.Factory(
                    query_handlers.ListWebhookDeliveryAttemptsForAppHandler,
                    repo=read_repos.app_child_read_repo,
                ),
                queries.ListAppInstallationsForAppQuery: providers.Factory(
                    query_handlers.ListAppInstallationsForAppHandler,
                    repo=read_repos.app_installation_read_repo,
                ),
                queries.GetAppInstallationForAppQuery: providers.Factory(
                    query_handlers.GetAppInstallationForAppHandler,
                    repo=read_repos.app_installation_read_repo,
                ),
                queries.ListUserAppInstallationsQuery: providers.Factory(
                    query_handlers.ListUserAppInstallationsHandler,
                    repo=read_repos.app_installation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOutgoingOrganizationRelationByTargetQuery: providers.Factory(
                    query_handlers.GetOutgoingOrganizationRelationByTargetHandler,
                    repo=read_repos.organization_relation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetEventReferenceQuery: providers.Factory(
                    query_handlers.GetEventReferenceHandler,
                    repo=read_repos.event_reference_read_repo,
                ),
                queries.ListOrganizationsForAdminQuery: providers.Factory(
                    query_handlers.ListOrganizationsForAdminHandler,
                    repo=read_repos.organization_admin_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOrganizationForAdminQuery: providers.Factory(
                    query_handlers.GetOrganizationForAdminHandler,
                    repo=read_repos.organization_admin_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOutgoingOrganizationRelationsQuery: providers.Factory(
                    query_handlers.ListOutgoingOrganizationRelationsHandler,
                    repo=read_repos.organization_relation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOutgoingOrganizationRelationQuery: providers.Factory(
                    query_handlers.GetOutgoingOrganizationRelationHandler,
                    repo=read_repos.organization_relation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListIncomingOrganizationVerificationRequestsQuery: providers.Factory(
                    query_handlers.ListIncomingOrganizationVerificationRequestsHandler,
                    repo=read_repos.organization_verification_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOutgoingOrganizationVerificationRequestsQuery: providers.Factory(
                    query_handlers.ListOutgoingOrganizationVerificationRequestsHandler,
                    repo=read_repos.organization_verification_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOutgoingOrganizationVerificationRequestQuery: providers.Factory(
                    query_handlers.GetOutgoingOrganizationVerificationRequestHandler,
                    repo=read_repos.organization_verification_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListIncomingEventReferenceRequestsQuery: providers.Factory(
                    query_handlers.ListIncomingEventReferenceRequestsHandler,
                    repo=read_repos.event_reference_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOutgoingEventReferenceRequestsQuery: providers.Factory(
                    query_handlers.ListOutgoingEventReferenceRequestsHandler,
                    repo=read_repos.event_reference_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetIncomingEventReferenceRequestReviewQuery: providers.Factory(
                    query_handlers.GetIncomingEventReferenceRequestReviewHandler,
                    repo=read_repos.event_reference_request_read_repo,
                    event_repo=read_repos.event_detail_read_repo,
                    authz=actor_authorization_service,
                    visibility=event_visibility_service,
                ),
                queries.GetOutgoingEventReferenceRequestQuery: providers.Factory(
                    query_handlers.GetOutgoingEventReferenceRequestHandler,
                    repo=read_repos.event_reference_request_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListIncomingEventReferencesQuery: providers.Factory(
                    query_handlers.ListIncomingEventReferencesHandler,
                    repo=read_repos.event_reference_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOutgoingEventReferencesQuery: providers.Factory(
                    query_handlers.ListOutgoingEventReferencesHandler,
                    repo=read_repos.event_reference_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetIncomingEventReferenceQuery: providers.Factory(
                    query_handlers.GetIncomingEventReferenceHandler,
                    repo=read_repos.event_reference_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUserOAuth2TokensQuery: providers.Factory(
                    query_handlers.ListUserOAuth2TokensHandler,
                    repo=read_repos.oauth2_token_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetUserOAuth2TokenQuery: providers.Factory(
                    query_handlers.GetUserOAuth2TokenHandler,
                    repo=read_repos.oauth2_token_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListAppInstallationsQuery: providers.Factory(
                    query_handlers.ListAppInstallationsHandler,
                    repo=read_repos.app_installation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetAppInstallationQuery: providers.Factory(
                    query_handlers.GetAppInstallationHandler,
                    repo=read_repos.app_installation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetInstallableAppQuery: providers.Factory(
                    query_handlers.GetInstallableAppHandler,
                    repo=read_repos.app_installation_read_repo,
                ),
                queries.GetAppWebhookDeliveryAttemptQuery: providers.Factory(
                    query_handlers.GetAppWebhookDeliveryAttemptHandler,
                    repo=read_repos.app_child_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListAppWebhookDeliveryAttemptsQuery: providers.Factory(
                    query_handlers.ListAppWebhookDeliveryAttemptsHandler,
                    repo=read_repos.app_child_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetAppWebhookDeliveryQuery: providers.Factory(
                    query_handlers.GetAppWebhookDeliveryHandler,
                    repo=read_repos.app_child_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListAppWebhookDeliveriesQuery: providers.Factory(
                    query_handlers.ListAppWebhookDeliveriesHandler,
                    repo=read_repos.app_child_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetAppKeyQuery: providers.Factory(
                    query_handlers.GetAppKeyHandler,
                    repo=read_repos.app_child_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListAppKeysQuery: providers.Factory(
                    query_handlers.ListAppKeysHandler,
                    repo=read_repos.app_child_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOAuth2ClientQuery: providers.Factory(
                    query_handlers.GetOAuth2ClientHandler,
                    repo=read_repos.oauth2_client_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOrganizationOAuth2ClientsQuery: providers.Factory(
                    query_handlers.ListOrganizationOAuth2ClientsHandler,
                    repo=read_repos.oauth2_client_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUserOAuth2ClientsQuery: providers.Factory(
                    query_handlers.ListUserOAuth2ClientsHandler,
                    repo=read_repos.oauth2_client_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListAppsQuery: providers.Factory(
                    query_handlers.ListAppsHandler,
                    repo=read_repos.oauth2_client_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetAppQuery: providers.Factory(
                    query_handlers.GetAppHandler,
                    repo=read_repos.oauth2_client_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetApiKeyQuery: providers.Factory(
                    query_handlers.GetApiKeyHandler,
                    repo=read_repos.api_key_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOrganizationApiKeysQuery: providers.Factory(
                    query_handlers.ListOrganizationApiKeysHandler,
                    repo=read_repos.api_key_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUserApiKeysQuery: providers.Factory(
                    query_handlers.ListUserApiKeysHandler,
                    repo=read_repos.api_key_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUserOrganizationInvitationsQuery: providers.Factory(
                    query_handlers.ListUserOrganizationInvitationsHandler,
                    repo=read_repos.organization_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetUserOrganizationInvitationQuery: providers.Factory(
                    query_handlers.GetUserOrganizationInvitationHandler,
                    repo=read_repos.organization_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOrganizationInvitationRecipientQuery: providers.Factory(
                    query_handlers.GetOrganizationInvitationRecipientHandler,
                    repo=read_repos.organization_invitation_read_repo,
                ),
                queries.ListOrganizationMemberInvitationsQuery: providers.Factory(
                    query_handlers.ListOrganizationMemberInvitationsHandler,
                    repo=read_repos.organization_member_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOrganizationMemberInvitationQuery: providers.Factory(
                    query_handlers.GetOrganizationMemberInvitationHandler,
                    repo=read_repos.organization_member_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUserMemberInvitationsQuery: providers.Factory(
                    query_handlers.ListUserMemberInvitationsHandler,
                    repo=read_repos.organization_member_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetUserMemberInvitationQuery: providers.Factory(
                    query_handlers.GetUserMemberInvitationHandler,
                    repo=read_repos.organization_member_invitation_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetMemberInvitationRecipientQuery: providers.Factory(
                    query_handlers.GetMemberInvitationRecipientHandler,
                    repo=read_repos.organization_member_invitation_read_repo,
                ),
                queries.ListOrganizationMembersQuery: providers.Factory(
                    query_handlers.ListOrganizationMembersHandler,
                    repo=read_repos.organization_member_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetOrganizationMemberQuery: providers.Factory(
                    query_handlers.GetOrganizationMemberHandler,
                    repo=read_repos.organization_member_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListUserOrganizationMembershipsQuery: providers.Factory(
                    query_handlers.ListUserOrganizationMembershipsHandler,
                    repo=read_repos.organization_member_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.GetUserOrganizationMembershipQuery: providers.Factory(
                    query_handlers.GetUserOrganizationMembershipHandler,
                    repo=read_repos.organization_member_read_repo,
                    authz=actor_authorization_service,
                ),
                queries.ListOrganizationMemberRolesQuery: providers.Factory(
                    query_handlers.ListOrganizationMemberRolesHandler,
                    repo=read_repos.organization_member_read_repo,
                ),
            }
        ),
    )

    query_bus = providers.Factory(
        QueryBus,
        app_context_provider=context.app_context_provider,
        query_handler_factory=query_handler_factory,
        read_session_scope=infrastructure.read_session_scope,
    )


class Application(containers.DeclarativeContainer):
    config = providers.Configuration()
    __self__ = providers.Self()

    infrastructure = providers.Container(Infrastructure)
    context = providers.Container(Context)
    read_repos = providers.Container(
        ReadRepos,
        infrastructure=infrastructure,
    )
    services = providers.Container(
        Services,
        config=config,
        read_repos=read_repos,
        infrastructure=infrastructure,
    )
    cqrs = providers.Container(
        Cqrs,
        infrastructure=infrastructure,
        context=context,
        services=services,
        read_repos=read_repos,
        config=config,
    )
