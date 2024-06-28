<script lang="ts">
  import LogoWhite from "$lib/img/logo/logo_frame_white.png";
  import LogoBlack from "$lib/img/logo/logo_frame.png";
  import Authentication from "$lib/img/wallpapers/authentication.jpg";
  import UserAuthForm from "$lib/components/login/user-auth-form.svelte";
  import { site } from "$lib/config";
</script>

<div class="md:hidden hidden">
  <img src={Authentication} alt="Authentication" class="block dark:hidden" />
  <img src={Authentication} alt="Authentication" class="hidden dark:block" />
</div>
<div
  class="container relative h-full flex-col items-center justify-center grid lg:max-w-none lg:grid-cols-2 lg:px-0 w-full"
>
  <div class="relative hidden h-full flex-col bg-muted p-10 text-white dark:border-r lg:flex">
    <div class="absolute inset-0 bg-cover" style="background-image: url({Authentication});" />
    <div class="relative z-20 flex items-center text-lg font-medium">
      <!-- <Command class="mr-2 h-6 w-6" /> -->
      <img src={LogoWhite} alt="spesr logo" class="h-6 w-6 mr-2" />
      {site.name}
    </div>
    <div class="relative z-20 mt-auto">
      <blockquote class="space-y-2">
        <p class="text-lg">
          &ldquo;{site.description}&rdquo;
        </p>
        <footer class="text-sm">Natron Tech AG</footer>
      </blockquote>
    </div>
  </div>
  <div class="lg:p-8">
    <div class="mx-auto flex w-full flex-col justify-center space-y-6 sm:w-[350px]">
      <div class="z-20 flex items-center font-medium justify-center">
        <!-- <Command class="mr-2 h-6 w-6" /> -->
        <img src={LogoBlack} alt="spesr logo" class="h-20 w-20 mr-2" />
      </div>
      <div class="flex flex-col space-y-2 text-center">
        <h1 class="text-2xl font-semibold tracking-tight">Welcome</h1>

        <p class="text-sm text-muted-foreground">Enter your email and password to log in.</p>
      </div>
      <UserAuthForm />
      <p class="px-8 text-center text-sm text-muted-foreground">
        By clicking continue, you agree to our
        <a href="/terms" class="underline underline-offset-4 active:text-primary">
          Terms of Service
        </a>
        and
        <a href="/privacy" class="underline underline-offset-4 active:text-primary">
          Privacy Policy
        </a>
        .
      </p>
    </div>
  </div>
</div>
