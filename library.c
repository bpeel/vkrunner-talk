#include <stdio.h>

#include <vkrunner/vkrunner.h>

int
main(int argc, char **argv)
{
    struct vr_source *source =
        vr_source_from_file("simple-example.shader_test");

    struct vr_config *config = vr_config_new();
    struct vr_executor *executor = vr_executor_new(config);

    enum vr_result result = vr_executor_execute(executor, source);

    vr_executor_free(executor);
    vr_config_free(config);

    vr_source_free(source);

    return result == VR_RESULT_FAIL ? EXIT_FAILURE : EXIT_SUCCESS;
}
